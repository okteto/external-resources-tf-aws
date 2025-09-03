package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/sqs"
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

func checkForMessages(ctx context.Context) {
	sdkConfig, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		fmt.Println("Couldn't load default configuration. Have you set up your AWS account?")
		panic(err)

	}
	sqsClient := sqs.NewFromConfig(sdkConfig)	
	
	for {
		select {
		case <-ctx.Done():
			fmt.Println("stop receiving messages")
			return
		default:
			msgResult, err := sqsClient.ReceiveMessage(ctx, &sqs.ReceiveMessageInput{
				QueueUrl:            aws.String(os.Getenv("QUEUE")),
				MaxNumberOfMessages: int32(5),
				WaitTimeSeconds:     int32(3),
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

				fmt.Printf("added order %s with %d items to pending orders", p.OrderID, len(p.Items))
				fmt.Println()

				_, err := sqsClient.DeleteMessage(ctx, &sqs.DeleteMessageInput{
					QueueUrl:      aws.String(os.Getenv("QUEUE")),
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
	ctx, cancel := context.WithCancel(context.Background())
	go checkForMessages(ctx)

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

	r.GET("/healthz", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":   "healthy",
			"hostname": os.Getenv("HOSTNAME"),
		})
	})

	r.GET("/orders", func(c *gin.Context) {
		fmt.Println("kitchen frontend connected, sending pending orders")
		
		// Always send all existing pending orders that are not ready
		var pendingToSend []PendingOrder
		for _, order := range pendingOrders {
			if !order.IsReady() {
				pendingToSend = append(pendingToSend, order)
			}
		}
		
		fmt.Printf("sending %d pending orders\n", len(pendingToSend))
		c.JSON(http.StatusOK, pendingToSend)
	})

	r.StaticFS("/public", http.Dir("public"))
	r.StaticFile("/", "./public/index.html")

	fmt.Println("ready to cook some grub 🔪")
	r.Run()
	cancel()
}
