/* eslint-disable no-console */
const { Client } = require('minio');

async function main() {
  const endpointVar = process.env.S3_ENDPOINT || 'http://localhost:9000';
  const endpoint = endpointVar.replace('http://', '').replace('https://', '');
  const useSSL = endpointVar.startsWith('https://');
  const accessKey = process.env.S3_ACCESS_KEY || 'minio';
  const secretKey = process.env.S3_SECRET_KEY || 'minio12345';
  const bucket = process.env.S3_BUCKET || 'fiber-photos';

  const minioClient = new Client({ endPoint: endpoint.split(':')[0], port: Number(endpoint.split(':')[1] || (useSSL ? 443 : 9000)), useSSL, accessKey, secretKey });

  const exists = await minioClient.bucketExists(bucket).catch(() => false);
  if (!exists) {
    await minioClient.makeBucket(bucket).catch((e) => console.error('makeBucket error', e));
  }
  console.log(`Bucket ${bucket} is ready`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

