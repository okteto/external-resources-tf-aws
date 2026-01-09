const express = require('express');
const os = require('os');
const { SQSClient, SendMessageCommand } = require("@aws-sdk/client-sqs");

const queue = process.env.QUEUE;
const sqsClient = new SQSClient({region: process.env.REGION});

const app = express();
const port = 3000;

// Set EJS as the view engine
app.set('view engine', 'ejs');
app.use(express.json());
app.use(express.static('public'))

// the values for the template
var templateValues = {
    title: "The Oktaco Shop",
    logo: "/oktaco.png",
    placeholder: "Tacos, burritos, churros...",
    emoji: "🌯"
};

// WARNING: Only remove the comments if you believe that pizzas are better than tacos
/* templateValues = {
    title: "The Okpizza Shop",
    logo: "/okpizza.png",
    placeholder: "Thin slice, neapolitan, deep dish...",
    emoji: "🍕"
};*/

app.get('/healthz', function (req, res) {
    res.json({
        "status": "200",
        "hostname": os.hostname()
    })
});

app.post('/order', function (req, res) {
    // Validate that the order has items
    if (!req.body.items || !Array.isArray(req.body.items) || req.body.items.length === 0) {
        return res.status(400).json({ error: "Cannot submit order without any items 🚫" });
    }

    const divertHeader = extractDivertKey(req, "okteto-divert");
    
    var params = {
        MessageBody: JSON.stringify(req.body),
        QueueUrl: queue,
    };

    if (divertHeader != "") { 
        params.MessageAttributes = {
            "okteto-divert": {
                DataType: "String",
                StringValue: divertHeader, // consumer identifier
            },
        }
    }

    sqsClient.send(new SendMessageCommand(params))
        .then(_ => {
            console.log(`order sent to the kitchen 👩🏼‍🍳👨🏻‍🍳`);
            res.sendStatus(201);
        })
        .catch(error => {
            console.error(error);
            res.sendStatus(500);
        });
})

function extractDivertKey(req, key) {
  const baggage = req.get("baggage");
  if (!baggage) {
    return "";
  }

  // Split on commas that separate members
  const members = baggage.split(",");

  for (const member of members) {
    const [k, v] = member.trim().split("=", 2);
    if (k === key && v) {
      // Per spec, baggage values may be URL-encoded
      try {
        return decodeURIComponent(v);
      } catch {
        return v;
      }
    }
  }
  return "";
}

// Define a route that renders the index.ejs template with a templated message
app.get('/', (req, res) => {
    res.render('index', templateValues);
});

// Start the server
app.listen(port, () => {
    console.log('ready to take your order 📝');
});