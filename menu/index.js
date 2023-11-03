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
    var params = {
        MessageBody: JSON.stringify(req.body),
        QueueUrl: queue
    };

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
// Define a route that renders the index.ejs template with a templated message
app.get('/', (req, res) => {
    res.render('index', templateValues);
});

// Start the server
app.listen(port, () => {
    console.log('ready to take your order 📝');
});