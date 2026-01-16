# API App foncière (CartoFoncier)

API pour la gestion des users et des notifications et l'authentification
Microservice pour les traitements SIG
Description du projet avec liens externes...

## Code Flow

Explication du fonctionnement global de l'application, des traitements SIG réalisé avec geopandas, les différents model de base de données utilisées$, etc.

## System requirements

* git
* Docker desktop

## Setup

First clone the repo
`git clone <this repo>
cd <repo name>`

run
`docker compose up`

The swagger generated documentation should be available at this address [](http://localhost:8080/docs#/) once the containers are running.

```mermaid
---
title: Architecture de CartoFoncier
---
flowchart TB
	DB[(Postgresql)]
	Bucket[(DB temporaire)]
	subgraph webApp[Interface Client]
		direction LR
		action((action))
		user --> action
	end 
	click webApp "https://github.com/Remi971/foncier_front" _blank
	subgraph data[Source de données]
		direction LR
		pciVecteur[PCI VEcteur]
		autre[autre]
	end
	subgraph datahandling[Gestion de la donnée]
		direction LR
		Microservice["Microservice (SIG)"]
		Microservice2[Microservice d'orchestration]
		data
		Bucket
	end
	webApp <--> API
	click API "https://github.com/Remi971/foncier_api" _blank
	click Microservice2 "https://github.com/Remi971/foncier_orchestration" _blank
	click Microservice "https://github.com/Remi971/foncier_sig" _blank
	
	API --> Microservice2
	Microservice2 --> data
	data --> Microservice2
	API <--> DB
	Microservice2 --> Bucket
	Microservice2 --> Microservice
	Microservice --> DB
	Microservice --> Bucket
	Microservice2 --> DB
```
