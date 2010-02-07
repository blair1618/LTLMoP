Name: # Full name of the robot
Pioneer upon Avon

Sensors: # Available binary sensor propositions
lightOn
senseBook
senseClothes
senseTrash

Actions: # Available binary actuator propositions
pickUp
drop
destroy

MotionControlHandler: # Module with continuous controller for moving between regions
handlers.motionControl.heatController

DriveHandler: # Module for converting a desired velocity vector to realistic motor commands
handlers.drive.diffDrive

### Below are settings for Scorpion08

OrcaVelocityHost:
10.0.0.189

OrcaVelocityPort:
13339

OrcaPositionGroup:
239.255.255.0

OrcaPositionPort:
40976
