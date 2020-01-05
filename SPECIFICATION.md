# Apodo - Software Design Document
#### Core Team: Elliott Maguire (@elliott-maguire), Moshe Uminer (@mosheduminer), Ahmmad Ismail (@blueray453)

## Section 1: Introduction

### 1.1 Overview
Apodo is a modular, multi-protocol, and production-capable web server library written in Python and Rust.

### 1.2 Context
This document is intended to declare and make available for amendment the high- and low-level designs of the software.

### 1.3 Scope
As an organization, Gennitria aims to generate software that is as accessible as it is effective. Writing a fast, extensible, and well-designed web server library will enable developers to move quickly in development, especially in tandem with other Gennitria software, and create highly-optimized applications.

### 1.4 Goals
- Design high-level abstractions that enable extensive hackability.
- Develop fast and efficient implementations that drive unparalleled processing speeds and miniscule resource footprints.
- Write clean, expressive, and well-documented code.

### 1.5 Milestones
This section describes the primary development milestones that the team will follow as it works. It is written as such to support an iterative but goal-based development procedure.

#### Gateway Implementation
The first step will be the design and development of a transport-layer server/socket controller for protocol conversion, or gateway. This base will allow for the implementaton of modular protocol packages.

Important Components:

- **Event loop control**; the generation and management of the server's core event loop(s).
- **Socket control**; the generation and management of the server's sockets.
- **Connection reception**; the reception and delivery of connections.

#### Protocol Implementations
Once the gateway is ready, development and testing can begin on initial protocol implementations. Officially supported protocols will include HTTP/1.x, 2, 3, and WebSockets. The package most likely to be completed first is HTTP/1.x as it is the most straightforward, and enables the other implementations (without requiring ALT-SVC).

All protocol implementations will follow the same specification fitting to the base gateway, such that they are all compatible, and development and use of third-party protocol packages is possible.

This standardization is enforced also to enable the parallel development of all officially supported protocols.

Important Components

- **Connection Control**; independent reception from the gateway and response control to the client.
- **Flow Control**; clean and accurate control of request/response/stream control, from reception from the gateway to response to the client.
- **Efficient Parsing**; the efficient processing of request/response data according to the protocol.

#### Execution Environment Implementation
Once at least one protocol is brought to a functional state, work will begin on the framework execution environment provided by the server.

## Section 2: Specification

The fully-detailed software specification is still being drafted by Elliott.