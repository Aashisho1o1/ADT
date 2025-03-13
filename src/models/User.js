const userSchema = new Schema({
    name: String,
    email: String,
    password: String,
    // ... other fields
});

// Recommended improvements:
// 1. Add proper indexing
// 2. Implement data validation
// 3. Add timestamps 