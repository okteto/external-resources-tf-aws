FROM golang:buster as dev

WORKDIR /usr/src/app
RUN go install github.com/codegangsta/gin@latest
COPY go.mod go.sum /usr/src/app/
RUN go mod tidy
COPY . . 
RUN --mount=type=cache,target=/root/.cache/go-build go build -o /usr/local/bin/kitchen

FROM busybox
WORKDIR /app
COPY --from=dev /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=dev  /usr/src/app/public /app/public
COPY --from=dev /usr/local/bin/kitchen /app/kitchen

EXPOSE 8080
CMD ["/app/kitchen"]