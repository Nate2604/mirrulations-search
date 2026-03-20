# Google OAuth Set-Up 
1. Go to Google Cloud Console
2. Sign in with your @moravian.edu account
3. In the project picker, select "new project"
    Project name: mirrulations-search
4. Configure OAuth Consent Screen
    App information:
        App Name: mirrulations-search
        User support email: <your email>
    Select Next
    Audience: Internal
    Select Next
    Contact Information
    Email addresses: <your email>
    Select Next
    Check the box in Finish
    Select Create
5. Create OAuth client
    Application Type: Web application
    Name: mirrulations-search
    Authorized Javascript Origins: http://localhost:80
    Authorized Redirect URIs: http://localhost:80
6. Save client ID
7. In clients, download client secret JSON

## Configuration
 
In both dev and prod, the system will get configuration options from a `.env` file. Edit your current `.env` file to include these following values. 
 
* `BASE_URL`: The base URL of your application. This must match one of the redirect URIs configured in the Google Cloud Console.
  * `http://localhost:80` in dev
  * `https://<your-subdomain>.moraviancs.click` in prod
* `GOOGLE_CLIENT_ID`: The OAuth 2.0 Client ID from Google Cloud Console
* `GOOGLE_CLIENT_SECRET`: The OAuth 2.0 Client Secret from Google Cloud Console
 
Template `.env` file (in dev and prod):
 
```
BASE_URL=<redirect-URI>
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
```
 
In prod you also need to have the following values for the **AWS DNS Subdomain System**:
* `USERNAME` - Your username in the AWS DNS Subdomain System
* `TOKEN` - The bearer token provided by the AWS DNS Subdomain System
* `LABEL` - This should be `mirrulations-search`
 
The username and token provide authentication when you register your IP on the EC2 instance. The username and label define the subdomain. For example, if the username is `colemanb` and the label is `mirrulations-search`, the system will register your IP as `colemanb-mirrulations-search.moraviancs.click`.
 
Template for extra `.env` values (in prod) — ADD these to the `.env` file:
 
```
USERNAME=<username>
TOKEN=<token>
LABEL=mirrulations-search
```
 
