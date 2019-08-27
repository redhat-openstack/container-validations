FROM fedora:30

# Install git and ansible
RUN yum install -y git ansible
RUN yum clean all

COPY init.sh /init.sh
RUN chmod 0755 /init.sh

# Create validation user
RUN useradd -c "Validation user" -m -s /bin/sh validation
USER validation
COPY inventory.yaml /home/validation/inventory.yaml
WORKDIR /home/validation
CMD ["/init.sh"]
