// Add Redis caching
const redis = require('redis');
const client = redis.createClient();

// Cache frequently accessed data 