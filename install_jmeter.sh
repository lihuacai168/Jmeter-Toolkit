#!/bin/zsh

# JMeter 安装和配置脚本
# 支持通过 Homebrew 或手动下载安装

set -e

echo "🚀 开始安装 JMeter..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否已安装 JMeter
check_jmeter() {
    if command -v jmeter &> /dev/null; then
        echo -e "${GREEN}✅ JMeter 已安装: $(jmeter -v 2>&1 | head -1)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  JMeter 未安装${NC}"
        return 1
    fi
}

# 通过 Homebrew 安装
install_via_homebrew() {
    echo -e "${BLUE}📦 使用 Homebrew 安装 JMeter...${NC}"

    # 检查是否安装了 Homebrew
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}❌ Homebrew 未安装，请先安装 Homebrew:${NC}"
        echo -e "${YELLOW}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
        return 1
    fi

    # 安装 JMeter
    brew install jmeter

    if check_jmeter; then
        echo -e "${GREEN}✅ JMeter 通过 Homebrew 安装成功${NC}"
        return 0
    else
        echo -e "${RED}❌ JMeter 安装失败${NC}"
        return 1
    fi
}

# 手动下载安装
install_manually() {
    echo -e "${BLUE}📥 手动下载安装 JMeter...${NC}"

    JMETER_VERSION="5.6.3"
    JMETER_DIR="/opt/jmeter"
    DOWNLOAD_URL="https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz"

    # 创建安装目录
    echo "创建安装目录: $JMETER_DIR"
    sudo mkdir -p $JMETER_DIR

    # 下载 JMeter
    echo "下载 JMeter $JMETER_VERSION..."
    cd /tmp
    curl -O $DOWNLOAD_URL

    # 解压
    echo "解压 JMeter..."
    tar -xzf apache-jmeter-${JMETER_VERSION}.tgz

    # 移动到安装目录
    echo "安装 JMeter..."
    sudo mv apache-jmeter-${JMETER_VERSION}/* $JMETER_DIR/
    sudo chmod +x $JMETER_DIR/bin/jmeter

    # 清理
    rm -f apache-jmeter-${JMETER_VERSION}.tgz
    rm -rf apache-jmeter-${JMETER_VERSION}

    echo -e "${GREEN}✅ JMeter 手动安装完成${NC}"
}

# 配置环境变量
configure_environment() {
    echo -e "${BLUE}⚙️  配置环境变量...${NC}"

    ZSHRC="$HOME/.zshrc"

    # 检测 JMeter 安装路径
    if [[ -d "/opt/homebrew/bin" ]] && [[ -f "/opt/homebrew/bin/jmeter" ]]; then
        JMETER_HOME="/opt/homebrew/Cellar/jmeter/$(ls /opt/homebrew/Cellar/jmeter/ | tail -1)/libexec"
        JMETER_BIN="/opt/homebrew/bin"
    elif [[ -d "/usr/local/bin" ]] && [[ -f "/usr/local/bin/jmeter" ]]; then
        JMETER_HOME="/usr/local/Cellar/jmeter/$(ls /usr/local/Cellar/jmeter/ | tail -1)/libexec"
        JMETER_BIN="/usr/local/bin"
    elif [[ -d "/opt/jmeter" ]]; then
        JMETER_HOME="/opt/jmeter"
        JMETER_BIN="/opt/jmeter/bin"
    else
        echo -e "${RED}❌ 无法找到 JMeter 安装路径${NC}"
        return 1
    fi

    echo "JMeter 安装路径: $JMETER_HOME"
    echo "JMeter 可执行文件路径: $JMETER_BIN"

    # 备份原有的 .zshrc
    if [[ -f "$ZSHRC" ]]; then
        cp "$ZSHRC" "${ZSHRC}.backup.$(date +%Y%m%d_%H%M%S)"
        echo "已备份 .zshrc 到 ${ZSHRC}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # 检查是否已经配置过
    if grep -q "JMETER_HOME" "$ZSHRC" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  JMeter 环境变量已存在，跳过配置${NC}"
    else
        # 添加环境变量到 .zshrc
        cat >> "$ZSHRC" << EOF

# JMeter Environment Variables
export JMETER_HOME="$JMETER_HOME"
export PATH="\$JMETER_HOME/bin:\$PATH"
EOF
        echo -e "${GREEN}✅ JMeter 环境变量已添加到 $ZSHRC${NC}"
    fi

    # 应用环境变量
    export JMETER_HOME="$JMETER_HOME"
    export PATH="$JMETER_HOME/bin:$PATH"

    echo -e "${GREEN}✅ 环境变量配置完成${NC}"
}

# 验证安装
verify_installation() {
    echo -e "${BLUE}🔍 验证 JMeter 安装...${NC}"

    # 重新加载 zsh 配置
    source ~/.zshrc 2>/dev/null || true

    if command -v jmeter &> /dev/null; then
        echo -e "${GREEN}✅ JMeter 命令可用${NC}"
        jmeter -v 2>&1 | head -3
        echo ""
        echo -e "${GREEN}🎉 JMeter 安装和配置成功！${NC}"
        echo -e "${BLUE}💡 使用方法:${NC}"
        echo -e "   ${YELLOW}jmeter -n -t test.jmx -l result.jtl${NC}  # 命令行执行"
        echo -e "   ${YELLOW}jmeter${NC}                              # 启动 GUI"
        echo ""
        echo -e "${BLUE}📝 重新启动终端或执行以下命令使环境变量生效:${NC}"
        echo -e "   ${YELLOW}source ~/.zshrc${NC}"
        return 0
    else
        echo -e "${RED}❌ JMeter 命令不可用，请检查安装${NC}"
        return 1
    fi
}

# 主函数
main() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}    JMeter 安装和配置脚本${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""

    # 检查是否已安装
    if check_jmeter; then
        echo -e "${GREEN}JMeter 已安装，配置环境变量...${NC}"
        configure_environment
        verify_installation
        return
    fi

    # 询问安装方式
    echo -e "${YELLOW}请选择安装方式:${NC}"
    echo "1) 通过 Homebrew 安装 (推荐)"
    echo "2) 手动下载安装"
    echo "3) 取消安装"
    echo ""
    echo -n "请输入选择 [1-3]: "
    read choice

    case $choice in
        1)
            if install_via_homebrew; then
                configure_environment
                verify_installation
            fi
            ;;
        2)
            if install_manually; then
                configure_environment
                verify_installation
            fi
            ;;
        3)
            echo -e "${YELLOW}取消安装${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
