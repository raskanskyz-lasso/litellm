import Image from '@theme/IdealImage';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Lasso Security

## Quick Start
### 1. Create a new Lasso Guard

Go to [Lasso Application](https://app.aim.security/inventory/custom-ai-apps) and create a new guard.

When prompted, select API option, and name your guard.


### 2. Configure your Lasso Guard policies

In the newly created guard's page, you can find a reference to the prompt policy center of this guard.

You can decide which detections will be enabled, and set the threshold for each detection.

### 3. Add Lasso Guardrail on your LiteLLM config.yaml 

Define your guardrails under the `guardrails` section
```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: openai/gpt-3.5-turbo
      api_key: os.environ/OPENAI_API_KEY

guardrails:
  - guardrail_name: lasso-protected-app
    litellm_params:
      guardrail: lasso
      mode: pre_call # 'during_call' is also available
      api_key: os.environ/LASSO_API_KEY
      deputies: os.environ/LASSO_DEPUTIES
```

Under the `api_key`, insert the API key you were issued. The key can be found in the guard's page.
You can also set `LASSO_API_KEY` as an environment variable.

By default, the `api_base` is set to `https://server.lasso.security`. If you are using a self-hosted deployment, you can set the `api_base` to your URL.

### 4. Start LiteLLM Gateway
```shell
litellm --config config.yaml
```

### 5. Make your first request

:::note
The following example depends on enabling *PII* detection in your guard.
You can adjust the request content to match different guard's policies.
:::

<Tabs>
<TabItem label="Successfully blocked request" value = "blocked">


```shell
curl -i http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "hi my email is ishaan@berri.ai"}
    ],
    "guardrails": ["lasso-protected-app"]
  }'
```

If configured correctly, since `ishaan@berri.ai` would be detected by the Lasso Guard as PII, you'll receive a response similar to the following with a `400 Bad Request` status code:

```json
{
  "error": {
    "message": "\"ishaan@berri.ai\" detected as email",
    "type": "None",
    "param": "None",
    "code": "400"
  }
}
```

</TabItem>

<TabItem label="Successfully permitted request" value = "allowed">

:::note
When using LiteLLM with virtual keys, an `Authorization` header with the virtual key is required.
:::

```shell
curl -i http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "hi what is the weather"}
    ],
    "guardrails": ["aim-protected-app"]
  }'
```

The above request should not be blocked, and you should receive a regular LLM response (simplified for brevity):

```json
{
  "model": "gpt-3.5-turbo-0125",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "I can’t provide live weather updates without the internet. Let me know if you’d like general weather trends for a location and season instead!",
        "role": "assistant"
      }
    }
  ]
}
```

</TabItem>


</Tabs>

# Advanced

Aim Guard provides user-specific Guardrail policies, enabling you to apply tailored policies to individual users.
To utilize this feature, include the end-user's email in the request payload by setting the `x-aim-user-email` header of your request.

```shell
curl -i http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-aim-user-email: ishaan@berri.ai" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "hi what is the weather"}
    ],
    "guardrails": ["aim-protected-app"]
  }'
```
