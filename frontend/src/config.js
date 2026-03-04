const config = {
  API_URL: import.meta.env.VITE_API_URL || 'https://YOUR_API_ID.execute-api.eu-west-1.amazonaws.com/prod',
  COGNITO_USER_POOL_ID: import.meta.env.VITE_COGNITO_USER_POOL_ID || 'eu-west-1_XXXXXXXXX',
  COGNITO_CLIENT_ID: import.meta.env.VITE_COGNITO_CLIENT_ID || 'XXXXXXXXXXXXXXXXXXXXXXXXXX',
  REGION: import.meta.env.VITE_AWS_REGION || 'eu-west-1',
};

export default config;
