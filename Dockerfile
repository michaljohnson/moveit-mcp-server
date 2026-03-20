FROM moveit/moveit2:main-rolling-tutorial-source
# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Refresh expired ROS 2 GPG key
RUN apt-get install -y curl gnupg2 lsb-release && \
    rm -rf /etc/apt/sources.list.d/ros2-latest.list && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -sc) main" | tee /etc/apt/sources.list.d/ros2.list && \
    apt-get update

# Install Python, venv support, and virtual framebuffer for headless testing
RUN apt-get install -y python3-pip python3-venv xvfb && \
    rm -rf /var/lib/apt/lists/*

# Create workspace
WORKDIR /workspace

# Create a virtual environment for the MCP server with system site packages
ENV VIRTUAL_ENV=/opt/mcp-venv
RUN python3 -m venv --system-site-packages ${VIRTUAL_ENV}
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip inside the venv
RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies into the venv
RUN pip install --no-cache-dir \
    "mcp>=0.9.0" \
    "pyyaml>=6.0" \
    "starlette>=0.27.0" \
    "uvicorn>=0.23.0"

# Copy MCP server code into the container
COPY . /workspace/moveit-mcp-server/

# Install the MCP server (editable mode inside venv)
RUN cd /workspace/moveit-mcp-server && \
    pip install --no-cache-dir -e ".[dev]"

# Source ROS setup and workspace in bashrc
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /root/.bashrc && \
    echo "if [ -f ~/ws_moveit/install/setup.bash ]; then source ~/ws_moveit/install/setup.bash; fi" >> /root/.bashrc

# Activate venv automatically in new shells
RUN echo "source $VIRTUAL_ENV/bin/activate" >> /root/.bashrc

# Add helpful aliases
RUN echo "alias launch-mcp='moveit-mcp-server'" >> /root/.bashrc

# Create a wrapper script that sources ROS before running the MCP server
RUN echo '#!/bin/bash\n\
source /opt/ros/${ROS_DISTRO}/setup.bash\n\
if [ -f ~/ws_moveit/install/setup.bash ]; then\n\
    source ~/ws_moveit/install/setup.bash\n\
fi\n\
source ${VIRTUAL_ENV}/bin/activate\n\
exec moveit-mcp-server "$@"' > /usr/local/bin/moveit-mcp-server-wrapper && \
    chmod +x /usr/local/bin/moveit-mcp-server-wrapper

# Expose port for SSE/HTTP transport
EXPOSE 8000

# Default command
CMD ["/bin/bash"]