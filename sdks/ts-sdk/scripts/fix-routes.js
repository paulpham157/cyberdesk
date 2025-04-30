const fs = require('fs');
const path = require('path');

// Fix the routes in the sdk.gen.ts file, replacing all :param with {param} (hey-api only supports {param} syntax)
const targetFile = path.join(__dirname, '../src/client/sdk.gen.ts');
if (!fs.existsSync(targetFile)) {
  console.error('Target file not found:', targetFile);
  process.exit(1);
}
let content = fs.readFileSync(targetFile, 'utf8');

// Replace all :param with {param}
content = content.replace(/:([a-zA-Z0-9_]+)/g, '{$1}');

fs.writeFileSync(targetFile, content);
console.log('Route parameters fixed in sdk.gen.ts'); 