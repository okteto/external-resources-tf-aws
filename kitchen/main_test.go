package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func init() {
	// Set Gin to test mode
	gin.SetMode(gin.TestMode)
}

func TestCreatePendingOrder(t *testing.T) {
	// Clear pending orders before test
	pendingOrders = make(map[string]PendingOrder)

	receiptHandle := "test-receipt-handle"
	orderID := "test-order-123"
	foodOrder := FoodOrder{
		Items: []string{"Taco", "Burrito", "Churro"},
	}

	pendingOrder := CreatePendingOrder(receiptHandle, orderID, foodOrder)

	assert.Equal(t, orderID, pendingOrder.OrderID)
	assert.Equal(t, receiptHandle, pendingOrder.ReceiptHandle)
	assert.Len(t, pendingOrder.Items, 3)

	// Check that all items are initially not ready
	for _, item := range pendingOrder.Items {
		assert.False(t, item.Ready)
	}

	// Check that the order was added to pendingOrders map
	storedOrder, exists := pendingOrders[orderID]
	assert.True(t, exists)
	assert.Equal(t, pendingOrder, storedOrder)
}

func TestPendingOrderIsReady(t *testing.T) {
	tests := []struct {
		name     string
		order    PendingOrder
		expected bool
	}{
		{
			name: "All items ready",
			order: PendingOrder{
				Items: []PendingOrderItem{
					{Name: "Taco", Ready: true},
					{Name: "Burrito", Ready: true},
				},
			},
			expected: true,
		},
		{
			name: "Some items not ready",
			order: PendingOrder{
				Items: []PendingOrderItem{
					{Name: "Taco", Ready: true},
					{Name: "Burrito", Ready: false},
				},
			},
			expected: false,
		},
		{
			name: "No items ready",
			order: PendingOrder{
				Items: []PendingOrderItem{
					{Name: "Taco", Ready: false},
					{Name: "Burrito", Ready: false},
				},
			},
			expected: false,
		},
		{
			name:     "Empty order",
			order:    PendingOrder{Items: []PendingOrderItem{}},
			expected: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.order.IsReady()
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestMarkItemReady(t *testing.T) {
	// Clear and setup pending orders
	pendingOrders = make(map[string]PendingOrder)
	
	orderID := "test-order-456"
	pendingOrders[orderID] = PendingOrder{
		OrderID: orderID,
		Items: []PendingOrderItem{
			{Name: "Taco", Ready: false},
			{Name: "Burrito", Ready: false},
		},
	}

	// Mark first item as ready
	foodReady := FoodReady{
		OrderID: orderID,
		Item:    "Taco",
	}

	MarkItemReady(foodReady)

	// Check that the item was marked as ready
	order := pendingOrders[orderID]
	assert.True(t, order.Items[0].Ready)
	assert.False(t, order.Items[1].Ready)

	// Mark second item as ready
	foodReady.Item = "Burrito"
	MarkItemReady(foodReady)

	// Check that both items are now ready
	order = pendingOrders[orderID]
	assert.True(t, order.Items[0].Ready)
	assert.True(t, order.Items[1].Ready)
}

func TestMarkItemReadyNonExistentOrder(t *testing.T) {
	// Clear pending orders
	pendingOrders = make(map[string]PendingOrder)

	foodReady := FoodReady{
		OrderID: "non-existent-order",
		Item:    "Taco",
	}

	// This should not panic and should handle gracefully
	MarkItemReady(foodReady)

	// Verify no orders were created
	assert.Len(t, pendingOrders, 0)
}

func TestReadyEndpoint(t *testing.T) {
	// Setup
	pendingOrders = make(map[string]PendingOrder)
	orderID := "test-order-789"
	pendingOrders[orderID] = PendingOrder{
		OrderID: orderID,
		Items: []PendingOrderItem{
			{Name: "Taco", Ready: false},
		},
	}

	// Create router
	r := gin.New()
	r.POST("/ready", func(c *gin.Context) {
		var ready FoodReady
		if err := c.BindJSON(&ready); err != nil {
			c.AbortWithStatus(500)
			return
		}
		MarkItemReady(ready)
		c.Status(200)
	})

	// Test valid request
	foodReady := FoodReady{
		OrderID: orderID,
		Item:    "Taco",
	}
	jsonData, _ := json.Marshal(foodReady)

	req, _ := http.NewRequest("POST", "/ready", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	assert.Equal(t, 200, w.Code)

	// Verify the item was marked as ready
	order := pendingOrders[orderID]
	assert.True(t, order.Items[0].Ready)
}

func TestReadyEndpointInvalidJSON(t *testing.T) {
	r := gin.New()
	r.POST("/ready", func(c *gin.Context) {
		var ready FoodReady
		if err := c.BindJSON(&ready); err != nil {
			c.AbortWithStatus(500)
			return
		}
		MarkItemReady(ready)
		c.Status(200)
	})

	// Test invalid JSON
	req, _ := http.NewRequest("POST", "/ready", bytes.NewBuffer([]byte("invalid json")))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	// Gin returns 400 for invalid JSON binding
	assert.Equal(t, 400, w.Code)
}

func TestFoodOrderStruct(t *testing.T) {
	// Test JSON marshaling/unmarshaling
	original := FoodOrder{
		Items: []string{"Taco", "Burrito", "Quesadilla"},
	}

	jsonData, err := json.Marshal(original)
	assert.NoError(t, err)

	var unmarshaled FoodOrder
	err = json.Unmarshal(jsonData, &unmarshaled)
	assert.NoError(t, err)

	assert.Equal(t, original.Items, unmarshaled.Items)
}

func TestFoodReadyStruct(t *testing.T) {
	// Test JSON marshaling/unmarshaling
	original := FoodReady{
		OrderID: "order-123",
		Item:    "Taco Supreme",
	}

	jsonData, err := json.Marshal(original)
	assert.NoError(t, err)

	var unmarshaled FoodReady
	err = json.Unmarshal(jsonData, &unmarshaled)
	assert.NoError(t, err)

	assert.Equal(t, original.OrderID, unmarshaled.OrderID)
	assert.Equal(t, original.Item, unmarshaled.Item)
}

func TestPendingOrderStruct(t *testing.T) {
	// Test JSON marshaling/unmarshaling
	original := PendingOrder{
		OrderID:       "order-456",
		ReceiptHandle: "receipt-handle-123", // This should be excluded from JSON
		Items: []PendingOrderItem{
			{Name: "Taco", Ready: true},
			{Name: "Burrito", Ready: false},
		},
	}

	jsonData, err := json.Marshal(original)
	assert.NoError(t, err)

	var unmarshaled PendingOrder
	err = json.Unmarshal(jsonData, &unmarshaled)
	assert.NoError(t, err)

	assert.Equal(t, original.OrderID, unmarshaled.OrderID)
	assert.Equal(t, original.Items, unmarshaled.Items)
	// ReceiptHandle should be empty due to json:"-" tag
	assert.Empty(t, unmarshaled.ReceiptHandle)
}