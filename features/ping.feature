Feature: Ping Endpoint
  In order to check if the service is alive
  As a system monitor
  I want a /ping endpoint that returns a health status

@resource:cpu=0.1,memory=128,storage=10,story_points=1
Scenario: Service responds to ping
  Given the service is running
  When I call GET /v1/ping
  Then I receive a 200 OK
  And the response contains "pong": true
  And the response includes "service" and "commit" fields
