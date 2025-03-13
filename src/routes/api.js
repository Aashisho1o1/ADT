// Add pagination
router.get('/disasters', async (req, res) => {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    // ... implement pagination logic
}); 