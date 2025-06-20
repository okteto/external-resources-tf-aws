const request = require('supertest');

// Mock AWS SQS before requiring the app
const mockSend = jest.fn();
const mockSQSClient = {
    send: mockSend
};

jest.mock("@aws-sdk/client-sqs", () => ({
    SQSClient: jest.fn(() => mockSQSClient),
    SendMessageCommand: jest.fn((params) => ({ input: params }))
}));

const { SQSClient, SendMessageCommand } = require("@aws-sdk/client-sqs");

describe('Menu Service', () => {
    let app;

    beforeAll(() => {
        // Set environment variables before requiring the app
        process.env.QUEUE = 'test-queue-url';
        process.env.REGION = 'us-east-1';
        
        // Require the app after setting environment and mocks
        app = require('./index.js');
    });

    beforeEach(() => {
        // Clear all mocks before each test
        jest.clearAllMocks();
    });

    afterAll(() => {
        // Clean up environment variables
        delete process.env.QUEUE;
        delete process.env.REGION;
    });

    describe('GET /healthz', () => {
        it('should return health status', async () => {
            const response = await request(app)
                .get('/healthz')
                .expect(200);

            expect(response.body).toHaveProperty('status', '200');
            expect(response.body).toHaveProperty('hostname');
            expect(typeof response.body.hostname).toBe('string');
        });
    });

    describe('GET /', () => {
        it('should render the index page with template values', async () => {
            const response = await request(app)
                .get('/')
                .expect(200);

            expect(response.text).toContain('The Oktaco Shop');
            expect(response.text).toContain('Tacos, burritos, churros...');
            expect(response.text).toContain('🌯');
        });
    });

    describe('POST /order', () => {
        it('should successfully send order to SQS queue', async () => {
            const orderData = {
                items: ['Taco', 'Burrito'],
                customer: 'John Doe'
            };

            // Mock successful SQS send
            mockSend.mockResolvedValue({});

            const response = await request(app)
                .post('/order')
                .send(orderData)
                .expect(201);

            // Verify SQS send was called
            expect(mockSend).toHaveBeenCalledTimes(1);
            
            // Verify the command was created with correct parameters
            const sendCall = mockSend.mock.calls[0][0];
            expect(sendCall.input.MessageBody).toBe(JSON.stringify(orderData));
            expect(sendCall.input.QueueUrl).toBe('test-queue-url');
        });

        it('should handle SQS errors gracefully', async () => {
            const orderData = {
                items: ['Taco'],
                customer: 'Jane Doe'
            };

            // Mock SQS error
            mockSend.mockRejectedValue(new Error('SQS Error'));

            const response = await request(app)
                .post('/order')
                .send(orderData)
                .expect(500);

            expect(mockSend).toHaveBeenCalled();
        });

        it('should handle empty order data', async () => {
            mockSend.mockResolvedValue({});

            const response = await request(app)
                .post('/order')
                .send({})
                .expect(400);

            expect(mockSend).toHaveBeenCalledTimes(0);
        });
    });

    describe('Static files', () => {
        it('should serve static files from public directory', async () => {
            const response = await request(app)
                .get('/style.css')
                .expect(200);

            expect(response.headers['content-type']).toMatch(/text\/css/);
        });
    });

    describe('Template Values', () => {
        it('should use taco theme by default', () => {
            // Test through the rendered output since template values are used in rendering
            return request(app)
                .get('/')
                .expect(200)
                .then(response => {
                    expect(response.text).toContain('The Oktaco Shop');
                    expect(response.text).toContain('/oktaco.png');
                    expect(response.text).toContain('Tacos, burritos, churros...');
                });
        });
    });
});