// access_tokens/static/js/calling.js

import { CommunicationIdentityClient } from '@azure/communication-identity';
import { CallClient } from '@azure/communication-calling';

const connectionString = 'YOUR_CONNECTION_STRING';
const identityClient = new CommunicationIdentityClient(connectionString);

async function startCall() {
    try {
        const tokenResponse = await identityClient.createUserAndToken(['voip']);
        const token = tokenResponse.token;
        const callClient = new CallClient();
        const callAgent = await callClient.createCallAgent(token);
        console.log("Call agent created");
        // Kullanıcı arayüzü kodları ve çağrı işlemleri burada yapılır.
    } catch (error) {
        console.error("Error creating call agent: ", error);
    }
}

startCall();
