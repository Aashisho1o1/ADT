// Add input validation middleware
const { body, validationResult } = require('express-validator');

const validateDisasterInput = [
    body('title').trim().notEmpty(),
    body('location').trim().notEmpty(),
    // ... more validation rules
]; 