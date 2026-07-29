FROM scratch
COPY sona /sona
COPY hello.sona /hello.sona
ENTRYPOINT ["/sona", "run", "/hello.sona", "--engine", "native"]
