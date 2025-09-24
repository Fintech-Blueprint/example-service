

Feature: Broken Ping Service

@resource:cpu=0.1,memory=128,storage=10,story_points=1
Scenario: Broken ping
  Given the service is running
  When I send "ping"
  Then I receive "pong" response
