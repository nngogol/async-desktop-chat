#!/bin/bash

# Package:
# origin: https://github.com/francoislaberge/diagrams
# Installation in shell
# $ sudo npm install -g diagrams



main(){

    echo start - `date`

    # clear previous session
    rm -rf svg
    mkdir svg

    ######################
    #                    #
    #                    #
    #      ___ _ __      #
    #     / _ \ '_ \     #
    #    |  __/ | | |    #
    #     \___|_| |_|    #
    #                    #
    #                    #
    ######################

    echo en version
    echo .
    diagrams sequence text/en/diagram-start.sequence    output/en.diagram-start.svg
    echo ..
    diagrams sequence text/en/diagram2_1.sequence       output/en.diagram2_1.svg
    echo ...
    diagrams sequence text/en/diagram2_2.sequence       output/en.diagram2_2.svg
    echo ....
    diagrams sequence text/en/diagram2_3.sequence       output/en.diagram2_3.svg


    ######################
    #                    #
    #                    #
    #     _ __ _   _     #
    #    | '__| | | |    #
    #    | |  | |_| |    #
    #    |_|   \__,_|    #
    #                    #
    #                    #
    ######################


    echo ru version
    echo .
    diagrams sequence text/ru/diagram-start.sequence    output/ru.diagram-start.svg
    echo ..
    diagrams sequence text/ru/diagram2_1.sequence       output/ru.diagram2_1.svg
    echo ...
    diagrams sequence text/ru/diagram2_2.sequence       output/ru.diagram2_2.svg
    echo ....
    diagrams sequence text/ru/diagram2_3.sequence       output/ru.diagram2_3.svg


    # convert svg to png
    for i in output/*.svg; do
        convert "$i" "$i.png"
    done
    # rm all svg
    rm output/*.svg

    echo end   - `date`
}

time main