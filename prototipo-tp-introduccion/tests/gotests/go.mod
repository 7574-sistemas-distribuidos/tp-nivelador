module github.com/7574-sistemas-distribuidos/tp-introduccion/tests/go

go 1.24.2

require github.com/7574-sistemas-distribuidos/tp-introduccion v0.0.0

replace github.com/7574-sistemas-distribuidos/tp-introduccion => ../../services/client

require github.com/stretchr/testify v1.12.0

require gopkg.in/yaml.v3 v3.0.1 // indirect
