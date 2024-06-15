import { CommunicationIdentityClient } from '@azure/communication-identity';
import { CallClient, CallAgent } from '@azure/communication-calling';

const connectionString = 'YOUR_CONNECTION_STRING';
const identityClient = new CommunicationIdentityClient(connectionString);

async function initializeCallAgent() {
  try {
    const tokenResponse = await identityClient.createUserAndToken(['voip']);
    const token = tokenResponse.token;
    const callClient = new CallClient();
    const callAgent = await callClient.createCallAgent(token);
    console.log("Call agent created");

    document.getElementById('start-call-button').disabled = false;
    document.getElementById('hangup-call-button').disabled = false;
    document.getElementById('accept-call-button').disabled = false;
    document.getElementById('start-video-button').disabled = false;
    document.getElementById('stop-video-button').disabled = false;
  } catch (error) {
    console.error("Error creating call agent: ", error);
  }
}

document.getElementById('initialize-call-agent').addEventListener('click', initializeCallAgent);
