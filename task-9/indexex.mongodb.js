use("ecommerce");

//db.sales.find()

//db.sales.getIndexes()

//db.sales.createIndex({ quantity: 1 });

//db.sales.getIndexes()

db.sales.find({ quantity: { $gt: 5 } })

db.sales.find({ quantity: { $gt: 5 } }).explain("executionStats")