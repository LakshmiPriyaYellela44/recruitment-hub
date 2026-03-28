import client from './api';

const subscriptionService = {
  upgradeSubscription: (data) => client.post('/subscription/upgrade', data),
};

export default subscriptionService;
