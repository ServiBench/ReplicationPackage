#############################################################################
######## CONFIGURATION ######################################################
#############################################################################

# Define the Name and Space of your Cloud Foundry organzation accordingly
# The Makefile assumes this namespace is selected using "ibmcloud fn property --namespace"
# and "ibmcloud targed" appropriately
CF_ORG_NAME := kaffemuehle@posteo.de
CF_ORG_SPACE := dev

#############################################################################
######## CONSTANT DEFINITON #################################################
#############################################################################

MYSQL_SERVICE_NAME := evtproc-sql
MYSQL_CREDENTIALS_NAME := evtproc-sql-creds

EVENT_STREAMS_SERVICE_NAME := evt-hub
EVENT_STREAMS_ALIAS_NAME := my-evt-hub
EVENT_STREAMS_CREDENTIALS_NAME := evt-hub-creds

EVENT_STREAMS_TEMPERATURE_EVENTS_TOPIC_NAME := temperature
EVENT_STREAMS_STATE_CHANGE_EVENTS_TOPIC_NAME := state-change
EVENT_STREAMS_FORECAST_EVENTS_TOPIC_NAME := forecast
EVENT_STREAMS_DB_INGEST_TOPIC_NAME := db-ingest

TEMPERATURE_TRIGGER_NAME := temp-trigger
FORECAST_TRIGGER_NAME := forecast-trigger
STATE_CHANGE_TRIGGER_NAME := statechange-trigger
DB_INGEST_TRIGGER_NAME := dbingest-trigger

KAFKA_BINDING_NAME := Bluemix_$(EVENT_STREAMS_ALIAS_NAME)_$(EVENT_STREAMS_CREDENTIALS_NAME)
KAFKA_BINDING_PATH := /$(CF_ORG_NAME)_$(CF_ORG_SPACE)/$(KAFKA_BINDING_NAME)/messageHubFeed

#############################################################################
######## MAKE STEPS #########################################################
#############################################################################

create_kafka:
	ibmcloud resource service-instance-create $(EVENT_STREAMS_SERVICE_NAME) messagehub standard eu-de
	ibmcloud resource service-alias-create $(EVENT_STREAMS_ALIAS_NAME) --instance-name $(EVENT_STREAMS_SERVICE_NAME)
	ibmcloud cf create-service-key $(EVENT_STREAMS_ALIAS_NAME) $(EVENT_STREAMS_CREDENTIALS_NAME) -c '{"role":"Manager"}'
	ibmcloud cf service-key $(EVENT_STREAMS_ALIAS_NAME) $(EVENT_STREAMS_CREDENTIALS_NAME) | tail -n +5 | jq > kafka_creds.json
	ibmcloud fn package refresh

sleep_30:
	sleep 30

create_topics: 
	ibmcloud es init
	ibmcloud es topic-create $(EVENT_STREAMS_DB_INGEST_TOPIC_NAME)
	ibmcloud es topic-create $(EVENT_STREAMS_FORECAST_EVENTS_TOPIC_NAME)
	ibmcloud es topic-create $(EVENT_STREAMS_STATE_CHANGE_EVENTS_TOPIC_NAME)
	ibmcloud es topic-create $(EVENT_STREAMS_TEMPERATURE_EVENTS_TOPIC_NAME)

# Create the Event Streams instance and the database before waiting 30 seconds to create the topics
create_resources: create_kafka create_database sleep_30 create_topics

create_database:
	ibmcloud cf create-service compose-for-mysql Standard $(MYSQL_SERVICE_NAME)
	ibmcloud cf create-service-key $(MYSQL_SERVICE_NAME) $(MYSQL_CREDENTIALS_NAME)
	ibmcloud cf service-key $(MYSQL_SERVICE_NAME) $(MYSQL_CREDENTIALS_NAME) | tail -n +5 | jq > sql_creds.json

install_deps:
	cd eventinserter/ && npm install
	cd format_temperature/ && npm install
	cd format_forecast/ && npm install
	cd format_state_change/ && npm install
	cd ingest/ && npm install
	cd latest/ && npm install
	cd list/ && npm install

package: clean install_deps
	mkdir out || true
	cd eventinserter/ && zip -r  ../out/eventinserter.zip *
	cd format_temperature/ && zip -r  ../out/format_temperature.zip *
	cd format_forecast/ && zip -r  ../out/format_forecast.zip *
	cd format_state_change/ && zip -r  ../out/format_state_change.zip *
	cd ingest/ && zip -r  ../out/ingest.zip *
	cd latest/ && zip -r  ../out/latest.zip *
	cd list/ && zip -r  ../out/list.zip *

clean:
	cd eventinserter/ && rm -rvf eventinserter/ || true
	cd format_temperature/ && rm -rvf format_temperature/ || true
	cd format_forecast/ && rm -rvf format_forecast/ || true
	cd format_state_change/ && rm -rvf format_state_change/ || true
	cd ingest/ && rm -rvf ingest/ || true
	cd latest/ && rm -rvf latest/ || true
	cd list/ && rm -rvf list/ || true
	rm -rv out/ || true

deploy_actions: package
	ibmcloud fn action create eventinserter --kind nodejs:10 out/eventinserter.zip -P sql_creds.json -a final true
	ibmcloud fn action create format-forecast --kind nodejs:10 out/format_forecast.zip -P kafka_creds.json -p binding_name $(KAFKA_BINDING_NAME) -a final true
	ibmcloud fn action create format-temperature --kind nodejs:10 out/format_temperature.zip -P kafka_creds.json -p binding_name $(KAFKA_BINDING_NAME) -a final true
	ibmcloud fn action create format-state-change --kind nodejs:10 out/format_state_change.zip -P kafka_creds.json -p binding_name $(KAFKA_BINDING_NAME) -a final true
	ibmcloud fn action create ingest --web true --kind nodejs:10 out/ingest.zip -P kafka_creds.json -p binding_name $(KAFKA_BINDING_NAME) -a final true
	ibmcloud fn action create list --web true --kind nodejs:10 out/list.zip -P sql_creds.json -a final true
	ibmcloud fn action create latest --web true --kind nodejs:10 out/latest.zip -P sql_creds.json -a final true

update_actions: package
	ibmcloud fn action update eventinserter --kind nodejs:10 out/eventinserter.zip -P sql_creds.json -a final true
	ibmcloud fn action update format-forecast --kind nodejs:10 out/format_forecast.zip -P kafka_creds.json -p binding_name $(KAFKA_BINDING_NAME) -a final true
	ibmcloud fn action update format-temperature --kind nodejs:10 out/format_temperature.zip -P kafka_creds.json -p binding_name $(KAFKA_BINDING_NAME) -a final true
	ibmcloud fn action update format-state-change --kind nodejs:10 out/format_state_change.zip -P kafka_creds.json -p binding_name $(KAFKA_BINDING_NAME) -a final true
	ibmcloud fn action update ingest --web true --kind nodejs:10 out/ingest.zip -P kafka_creds.json -p binding_name $(KAFKA_BINDING_NAME) -a final true
	ibmcloud fn action update list --web true --kind nodejs:10 out/list.zip -P sql_creds.json -a final true
	ibmcloud fn action update latest --web true --kind nodejs:10 out/latest.zip -P sql_creds.json -a final true

create_triggers:
	ibmcloud fn trigger create $(FORECAST_TRIGGER_NAME) -f $(KAFKA_BINDING_PATH) -p topic $(EVENT_STREAMS_FORECAST_EVENTS_TOPIC_NAME) -p isJSONData true
	ibmcloud fn trigger create $(TEMPERATURE_TRIGGER_NAME) -f $(KAFKA_BINDING_PATH) -p topic $(EVENT_STREAMS_TEMPERATURE_EVENTS_TOPIC_NAME) -p isJSONData true
	ibmcloud fn trigger create $(STATE_CHANGE_TRIGGER_NAME) -f $(KAFKA_BINDING_PATH) -p topic $(EVENT_STREAMS_STATE_CHANGE_EVENTS_TOPIC_NAME) -p isJSONData true
	ibmcloud fn trigger create $(DB_INGEST_TRIGGER_NAME) -f $(KAFKA_BINDING_PATH) -p topic $(EVENT_STREAMS_DB_INGEST_TOPIC_NAME) -p isJSONData true

create_rules: 
	ibmcloud fn rule create $(TEMPERATURE_TRIGGER_NAME)-rule $(TEMPERATURE_TRIGGER_NAME) format-temperature
	ibmcloud fn rule create $(FORECAST_TRIGGER_NAME)-rule $(FORECAST_TRIGGER_NAME) format-forecast
	ibmcloud fn rule create $(STATE_CHANGE_TRIGGER_NAME)-rule $(STATE_CHANGE_TRIGGER_NAME) format-state-change
	ibmcloud fn rule create $(DB_INGEST_TRIGGER_NAME)-rule $(DB_INGEST_TRIGGER_NAME) eventinserter

create_api:
	ibmcloud fn api create /evtproc /list get list --response-type http
	ibmcloud fn api create /evtproc /latest get latest --response-type http
	ibmcloud fn api create /evtproc /ingest post ingest --response-type http
