#!/bin/bash


bold="\033[1m"

pink="\033[38;2;255;105;180m"
red="\033[31m"
green="\033[32m"
g=$green
blue="\033[34m"
yellow="\033[33m"

reset="\033[0m"
r=$reset

prefix="${green}${bold}>> ${reset}"


echo -e "
 ________________________________________
/ Мы займёмся установкой твоего клиента. \\
| Прсото следуй инструкциям. И никто не  |
\ пострадает.                            /
 ----------------------------------------
     \\
      \\ ${green}
          ${r}oO${g})-.                       .-(${r}Oo${g}
         /__  _\                     /_  __\\
         \  \(  |     ()~()         |  )/  /
          \__|\ |    (-___-)        | /|__/
          '  '--'    ==\`-'==        '--'  '
${reset}\
"   

function check_continue() {
    local software_name=$1
    echo -e -n "${red}>>>${r} Установить $software_name? [${g}y${r}/${red}N${r}]: "
    read answer
    case $answer in
        [Yy]* )
            echo -e "${prefix} Устанавливаем $software_name..."
            ;;
        * )
            echo -e "${prefix} Установка отменена. Выход из установщика."
            rm inst.sh
            echo -e "${prefix} Инсталлятор удалён"
            exit 1
            ;;
    esac
    echo
}


echo
if ! command -v python3 &> /dev/null; then
    echo -e "${prefix} ${blue}python3${reset} не найден."
    check_continue "${blue}python3${reset}"
    sudo apt update
    sudo apt install python3
    echo -e "${prefix} ${blue}python3${reset} установлен."
else
    echo -e "${prefix} ${blue}python3${reset} уже установлен."
fi


if ! command -v python -m venv &> /dev/null; then
    echo -e "${prefix} ${blue}python3-venv${reset} не найден."
    check_continue "${blue}python3-venv${reset}"
    sudo apt update
    sudo apt install python3-venv
    echo -e "${prefix} ${blue}python3-venv${reset} установлен."
else
    echo -e "${prefix} ${blue}python3-venv${reset} уже установлен."
fi


echo
check_continue "${blue}bjkolmp${reset} папку клиента"
if [ -d "./bjkolmp" ]; then
    echo -e "${prefix} Папка существует, удаляем"
    rm -r "./bjkolmp"
fi


mkdir "./bjkolmp"
echo -e "${prefix} Папка с клиентом установлена: ${blue}./bjkolmp${reset}"


cd "./bjkolmp"


echo
echo -e "${prefix} Скачиваем клиент..."
echo
curl http://localhost/clients/python/ws_python.py -o client.py
echo
curl http://localhost/clients/python/linux_req.txt -o requirements.txt


echo
echo -e "${prefix} Устанавливаем зависимости..."
python3 -m venv VENV
source ./VENV/bin/activate
pip install -r requirements.txt

cd ..

rm inst.sh
echo -e "${prefix} Инсталлятор удалён"

echo
echo -e "${prefix} Теперь вы можете запустить наше приложение!"
echo -e "${prefix} ${yellow}./bjkolmp/VENV/bin/python3 ./bjkolmp/client.py${reset}"

