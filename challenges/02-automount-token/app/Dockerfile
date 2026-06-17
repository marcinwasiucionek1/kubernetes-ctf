FROM python:3.12

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      ncat \
    && KUBECTL_VERSION=v1.36.2 \
    && curl -sSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
         -o /usr/local/bin/kubectl \
    && chmod +x /usr/local/bin/kubectl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY countries.csv app.py ./
COPY templates/ templates/
COPY static/ static/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
