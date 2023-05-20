package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/sqs"
	"github.com/gin-gonic/gin"
)

var (
	pendingOrders map[string]PendingOrder = map[string]PendingOrder{}
)

type FoodOrder struct {
	Items []string `json:"items"`
}

type FoodReady struct {
	OrderID string `json:"orderId"`
	Item    string `json:"item"`
}

type PendingOrder struct {
	OrderID       string             `json:"orderId"`
	ReceiptHandle string             `json:"-"`
	Items         []PendingOrderItem `json:"items"`
}

type PendingOrderItem struct {
	Name  string `json:"name"`
	Ready bool   `json:"ready"`
}

func CreatePendingOrder(receiptHandle string, orderID string, f FoodOrder) PendingOrder {
	p := PendingOrder{
		OrderID:       orderID,
		ReceiptHandle: receiptHandle,
		Items:         make([]PendingOrderItem, len(f.Items)),
	}

	for i := range f.Items {
		p.Items[i] = PendingOrderItem{
			Name:  f.Items[i],
			Ready: false,
		}
	}

	pendingOrders[orderID] = p

	return p
}

func MarkItemReady(f FoodReady) {
	if k, ok := pendingOrders[f.OrderID]; ok {
		for i := range k.Items {
			if pendingOrders[f.OrderID].Items[i].Name == f.Item {
				pendingOrders[f.OrderID].Items[i].Ready = true
				fmt.Printf("Item '%s' from Order '%s' is ready 🍽️", f.Item, f.OrderID)
				fmt.Println()
			}
		}

		if k.IsReady() {
			fmt.Printf("Order '%s' is ready 🛎️!", f.OrderID)
			fmt.Println()
			k.OrderCheck()
		}

		return
	}

	fmt.Printf("%s wasn't in the order list", f.OrderID)
	fmt.Println()
}

func (p *PendingOrder) OrderCheck() {
	checkServiceUrl := os.Getenv("CHECK")
	buff := new(bytes.Buffer)
	json.NewEncoder(buff).Encode(p)

	r, err := http.Post(checkServiceUrl, "application/json", buff)
	if err != nil {
		fmt.Printf("failed to order check: %s", err)
		fmt.Println()
		return
	}

	if r.StatusCode >= 400 {
		fmt.Printf("failed to order check: %d %s", r.StatusCode, r.Status)
		fmt.Println()
		return
	}

	fmt.Printf("Ordered check for %s 🧮", p.OrderID)
	fmt.Println()
}

func (p *PendingOrder) IsReady() bool {
	for _, i := range p.Items {
		if !i.Ready {
			return false
		}
	}

	return true
}

func checkForMessages(ctx context.Context, messages chan PendingOrder) {
	sess := session.Must(session.NewSessionWithOptions(session.Options{}))
	svc := sqs.New(sess)
	urlResult, err := svc.GetQueueUrl(&sqs.GetQueueUrlInput{
		QueueName: aws.String(os.Getenv("QUEUE")),
	})

	if err != nil {
		panic(err)
	}

	queueURL := urlResult.QueueUrl

	for {
		select {
		case <-ctx.Done():
			fmt.Println("stop receiving messages")
			return
		default:
			msgResult, err := svc.ReceiveMessage(&sqs.ReceiveMessageInput{
				QueueUrl:            queueURL,
				MaxNumberOfMessages: aws.Int64(5),
				WaitTimeSeconds:     aws.Int64(3),
			})

			if err != nil {
				fmt.Println(err)
				break
			}

			if len(msgResult.Messages) == 0 {
				continue
			}

			fmt.Printf("received %d messages from the queue", len(msgResult.Messages))
			fmt.Println()

			for _, m := range msgResult.Messages {

				var order FoodOrder
				if err := json.Unmarshal([]byte(*m.Body), &order); err != nil {
					fmt.Printf("failed to unmarshall the message: %s", err)
					fmt.Println()
					break
				}

				p := CreatePendingOrder(*m.ReceiptHandle, *m.MessageId, order)

				fmt.Printf("sending order %s with %d items to the kitchen", p.OrderID, len(p.Items))
				fmt.Println()

				messages <- p

				_, err := svc.DeleteMessage(&sqs.DeleteMessageInput{
					QueueUrl:      queueURL,
					ReceiptHandle: m.ReceiptHandle,
				})

				if err != nil {
					fmt.Printf("failed to delete message %s: %s", *m.MessageId, err)
					fmt.Println()
				}
			}
		}
	}
}

func main() {
	pendingMessages := make(chan PendingOrder, 1024)

	ctx, cancel := context.WithCancel(context.Background())
	go checkForMessages(ctx, pendingMessages)

	r := gin.Default()
	r.SetTrustedProxies(nil)

	r.POST("/ready", func(c *gin.Context) {
		var ready FoodReady
		if err := c.BindJSON(&ready); err != nil {
			fmt.Println(err)
			c.AbortWithStatus(500)
		}

		MarkItemReady(ready)
		c.Status(200)
	})

	r.GET("/orders", func(c *gin.Context) {
		fmt.Println("waiting for new orders")
		ticker := time.Tick(time.Duration(15) * time.Second)

		select {
		case <-c.Done():
		case <-c.Request.Context().Done():
			log.Printf("Received context cancel")
			c.AbortWithStatus(http.StatusRequestTimeout)
			return
		case m := <-pendingMessages:
			c.JSON(http.StatusOK, m)
			fmt.Println("order sent to the kitchen")
			return
		case <-ticker:
			c.AbortWithStatus(http.StatusRequestTimeout)
			return
		}

	})

	r.StaticFS("/public", http.Dir("public"))
	r.StaticFile("/", "./public/index.html")

	fmt.Println("ready to cook some grub 🔪")
	r.Run()
	cancel()
}
