"""Calculatrice scientifique : streamlit run app.py."""
import ast
import math
import operator

import streamlit as st


def calculate(expression: str, degrees: bool = False) -> float:
    """Évalue uniquement les nombres, opérateurs et fonctions autorisés."""
    expression = expression.strip()
    if not expression:
        raise ValueError("Saisissez une expression à calculer.")
    if len(expression) > 500:
        raise ValueError("Expression trop longue (500 caractères maximum).")
    expression = (expression.replace("^", "**").replace("π", "pi")
                  .replace("×", "*").replace("÷", "/").replace("−", "-"))
    angle = math.radians if degrees else lambda x: x
    inverse = math.degrees if degrees else lambda x: x

    def tangent(x):
        x = angle(x)
        if abs(math.cos(x)) < 1e-15:
            raise ValueError("La tangente n’est pas définie pour cet angle.")
        return math.tan(x)

    functions = {
        "sin": lambda x: math.sin(angle(x)),
        "cos": lambda x: math.cos(angle(x)), "tan": tangent,
        "asin": lambda x: inverse(math.asin(x)),
        "acos": lambda x: inverse(math.acos(x)),
        "atan": lambda x: inverse(math.atan(x)),
        "sqrt": math.sqrt, "ln": math.log, "log": math.log10,
        "log10": math.log10, "exp": math.exp, "abs": abs,
    }
    operations = {ast.Add: operator.add, ast.Sub: operator.sub,
                  ast.Mult: operator.mul, ast.Div: operator.truediv,
                  ast.Pow: operator.pow, ast.Mod: operator.mod}

    def finite(value):
        if isinstance(value, complex) or not math.isfinite(value):
            raise ValueError("Le résultat doit être un nombre réel fini.")
        return float(value)

    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return finite(node.value)
        if isinstance(node, ast.Name) and node.id in ("pi", "e"):
            return getattr(math, node.id)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            return finite(operations[type(node.op)](visit(node.left), visit(node.right)))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in functions and len(node.args) == 1 and not node.keywords):
            return finite(functions[node.func.id](visit(node.args[0])))
        raise ValueError("Expression non autorisée. Consultez les fonctions disponibles.")

    try:
        tree = ast.parse(expression, mode="eval")
        if sum(1 for _ in ast.walk(tree)) > 200:
            raise ValueError("Expression trop complexe. Simplifiez le calcul.")
        return visit(tree.body)
    except SyntaxError:
        raise ValueError("Syntaxe incorrecte : vérifiez les opérateurs et les parenthèses.") from None
    except ZeroDivisionError:
        raise ValueError("Division par zéro impossible.") from None
    except OverflowError:
        raise ValueError("Nombre trop grand pour être calculé.") from None
    except RecursionError:
        raise ValueError("Expression trop imbriquée. Simplifiez le calcul.") from None
    except ValueError as error:
        if str(error) == "math domain error":
            raise ValueError("Valeur hors domaine : vérifiez la racine, le logarithme ou la fonction inverse.") from None
        raise


def main():
    st.set_page_config(page_title="Calculatrice scientifique", page_icon="🧮", layout="centered")
    st.title("🧮 Calculatrice scientifique")
    st.caption("Des calculs simples aux fonctions scientifiques, dans une seule expression.")
    st.session_state.setdefault("history", [])

    with st.form("calculator"):
        mode = st.radio("Unité des angles", ["Radians", "Degrés"], horizontal=True)
        expression = st.text_input("Expression", value="sqrt(25) + 2^3", max_chars=500,
                                   placeholder="Exemple : sin(pi/2) + ln(e)")
        st.caption("Utilisez un point pour les décimales et * pour multiplier : 2*pi, 1.5*4.")
        submitted = st.form_submit_button("Calculer", type="primary", width="stretch")

    if submitted:
        try:
            result = calculate(expression, degrees=mode == "Degrés")
            formatted = format(result, ".15g")
            st.success(f"Résultat : {formatted}")
            st.caption(f"Calcul : {expression} · {mode}")
            st.session_state.history.insert(0, {"Expression": expression, "Résultat": formatted, "Angles": mode})
            st.session_state.history = st.session_state.history[:10]
        except ValueError as error:
            st.error(str(error))

    with st.expander("Fonctions et exemples", expanded=True):
        st.markdown("""
| Calcul | Syntaxe / exemple |
| :--- | :--- |
| Opérations et parenthèses | `(2 + 3) * 4 / 2 - 1` |
| Puissance, racine carrée | `2^3` ou `2**3`, `sqrt(25)` |
| Trigonométrie | `sin(x)`, `cos(x)`, `tan(x)` |
| Trigonométrie inverse | `asin(x)`, `acos(x)`, `atan(x)` |
| Logarithmes | `ln(e)` (naturel), `log(100)` ou `log10(100)` (base 10) |
| Exponentielle, valeur absolue | `exp(2)`, `abs(-5)` |
| Constantes | `pi` ou `π`, `e` |
| Reste de division | `10 % 3` |
""")
        st.info("Radians : sin(pi/2) = 1. Degrés : sin(90) = 1. "
                "Les fonctions inverses renvoient aussi l’unité choisie.")
        st.caption("Calculs réels à précision flottante. Les puissances sont prioritaires : "
                   "-2^2 = -4 ; (-2)^2 = 4. % est le modulo, pas un pourcentage.")

    if st.session_state.history:
        st.subheader("Historique")
        st.dataframe(st.session_state.history, hide_index=True, width="stretch")
        st.caption("Les 10 derniers calculs de cette session.")
        if st.button("Effacer l’historique"):
            st.session_state.history = []
            st.rerun()


if __name__ == "__main__":
    main()
