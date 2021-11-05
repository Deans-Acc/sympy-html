#/bin/python

import asyncio
import os
import pydoc
from tokenize import TokenError
from typing import List

import sympy
from sympy.parsing.sympy_parser import *
import pint
import websockets

import socket

ERRORS = (SyntaxError, TokenError, AttributeError, TypeError, ValueError)


def parse(arg: str, symbols: List):
    return sympy.parsing.sympy_parser.parse_expr(arg, local_dict=symbols, transformations=trans)


trans = (standard_transformations +
         (implicit_multiplication_application, function_exponentiation))


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Reserved ip address space for examples (NO NEED TO CHANGE)
        s.connect(('192.0.2.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


allowed_ips = [get_ip(), '127.0.0.1']

print("Url: " + allowed_ips[0] + ":8000")

if not os.path.isdir("saves"):
    if os.path.exists("saves"):
        print("saves exists as a not folder!")
        exit(1)
    os.mkdir("saves")


async def serve_websocket(ws, path):
    if not ws.remote_address[0] in allowed_ips:
        print("Fail: " + str(ws.remote_address))
        return
    symbols = {}
    # Alpha is recognized as a greek letter without change, but beta and gamma need to be switched with some functions
    symbols["beta"] = sympy.Symbol("beta")
    symbols["gamma"] = sympy.Symbol("gamma")
    symbols["Beta"] = sympy.parsing.sympy_parser.parse_expr("beta")
    symbols["Gamma"] = sympy.parsing.sympy_parser.parse_expr("gamma")

    symbols["ureg"] = pint.UnitRegistry()

    print_pretty = False
    try:
        async for message in ws:
            if message.startswith("Symbol "):
                syms = message.split(" ")[1:]
                for sym in syms:
                    symbols[sym] = sympy.Symbol(sym)
                await ws.send("Ok")

            elif message.startswith("Function "):
                syms = message.split(" ")[1:]
                for sym in syms:
                    symbols[sym] = sympy.Function(sym)
                await ws.send("Ok")

            elif message.startswith("Define "):
                if len(message.split(" ")) < 3:
                    await ws.send("Invalid input")
                    continue
                symbol = message.split(" ")[1]
                value = " ".join(message.split(" ")[2:])
                try:
                    symbols[symbol] = parse(value, symbols)
                    await ws.send(str(symbols[symbol]))
                except ERRORS as e:
                    await ws.send(f"Err: {str(e)}")

            elif message.startswith("Delete "):
                syms = message.split(" ")[1:]
                for sym in syms:
                    try:
                        del symbols[sym]
                    except KeyError:
                        pass
                await ws.send("Ok")

            elif message == "pretty":
                print_pretty = True
                await ws.send("Ok")

            elif message == "nopretty":
                print_pretty = False
                await ws.send("Ok")

            elif message.startswith("Help"):
                await ws.send("""Symbol argN - defines argN as symbol
Function argN - defines argN as function
Define sym val - defines sym as val
Delete argN - undefines argN
Info func - Returns info about func
List obj [filter] - List all attributes of obj with optional filter
Trust ip - Allow ip(v4) to use the websocket until kernel reboot
                    
ans - Last answer as Variable
ureg - Unit converter from pint""")

            elif message.startswith("Info "):
                try:
                    # Often doesn't work, for example with sin (To be expected with the lambda auto defined)
                    thing = parse(message.split(" ")[1], symbols)
                    await ws.send(pydoc.getdoc(thing))
                except ERRORS as e:
                    await ws.send(f"Err: {str(e)}")

            elif message.startswith("List "):
                try:
                    things = dir(parse(message.split(" ")[1], symbols))
                    filter = ""
                    if len(message.split(" ")) > 2:
                        filter = message.split(" ")[2]
                    two = []
                    one = []
                    thing = []
                    for t in things:
                        if not filter in t:
                            continue
                        if t.startswith("__"):
                            two.append(t)
                        elif t.startswith("_"):
                            one.append(t)
                        else:
                            thing.append(t)
                    await ws.send(str(two)+"\n"+str(one)+"\n"+str(thing))
                except ERRORS as e:
                    await ws.send(f"Err: {str(e)}")

            elif message.startswith("Trust "):
                allowed_ips.append(message.split(" ")[1])
                await ws.send("Ok")

            elif message.startswith("Save "):
                name = message.split(" ")[1]
                if "." in name or "/" in name or "\\" in name or name.strip() == "":
                    await ws.send("Err: Invalid file name")
                    continue
                filename = os.path.join("saves", name)
                if os.path.exists(filename):
                    await ws.send("Err: File already exists")
                    continue
                with open(filename, "w") as file:
                    file.write(" ".join(message.split(" ")[2:]))
                    await ws.send("Success")

            elif message.startswith("Load "):
                name = message.split(" ")[1]
                if "." in name or "/" in name or "\\" in name or name.strip() == "":
                    await ws.send("Err: Invalid file name")
                    continue
                filename = os.path.join("saves", name)
                if not os.path.exists(filename):
                    await ws.send("Err: File doesn't exist")
                    continue
                with open(filename, "r") as file:
                    await ws.send(file.read())

            else:
                try:
                    answer = parse(message, symbols)
                    symbols["ans"] = answer
                    if print_pretty:
                        await ws.send(sympy.pretty(answer, use_unicode=True))
                    else:
                        await ws.send(str(answer))
                except ERRORS as e:
                    await ws.send(f"Err: {str(e)}")
    except Exception as e:
        print(f"Websocket went wrong: {str(e)}")


async def main():
    async with websockets.serve(serve_websocket, "0.0.0.0", 8001):
        await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
