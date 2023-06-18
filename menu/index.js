const express = require('express')
const os = require('os')
const { SQSClient, SendMessageCommand } = require("@aws-sdk/client-sqs");
const sqsClient = new SQSClient({region: process.env.REGION});
const author = process.env.AUTHOR;
const queue = process.env.QUEUE;

const app = express()
app.use(express.json());
app.use(express.static('public'))

app.get('/healthz', function (req, res) {
  res.json({
    "status": "200",
    "hostname": os.hostname()
  })
})

app.post('/order', function (req, res) {
  var params = {
   MessageBody: JSON.stringify(req.body),
   QueueUrl: queue
 };

 sqsClient.send(new SendMessageCommand(params))
  .then(data => {
    console.log(`order sent to the kitchen 👩🏼‍🍳👨🏻‍🍳`);
    res.sendStatus(201);
  })
  .catch(error => {
    console.error(error);
    res.sendStatus(500);
  });
})


console.log('ready to take your order 📝');
app.listen(3000)