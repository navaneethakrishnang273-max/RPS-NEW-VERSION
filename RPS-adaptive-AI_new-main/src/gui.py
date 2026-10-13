"""
Native Desktop GUI for Rock-Paper-Scissors Opponent Modeling
=============================================================
A pure-Python Tkinter desktop window for playing live against the Markov AI.
Includes built-in speech synthesis (TTS) and accessible hotkeys for visually impaired users.
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rps_agent import AdaptiveAgent, COUNTER_MOVES, MOVE_NAMES, evaluate_round


def speak_async(text: str):
    """Speaks text asynchronously using Windows SAPI without blocking UI."""
    def _speak():
        try:
            safe_text = text.replace('"', '`"')
            cmd = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Rate = 1; $synth.Speak("{safe_text}")'
            subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                capture_output=True,
                timeout=12,
            )
        except Exception:
            pass

    threading.Thread(target=_speak, daemon=True).start()


class RPSDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RPS Markov Opponent Modeling AI — Accessible Edition")
        self.root.geometry("660x720")
        self.root.configure(bg="#0f172a")
        self.root.resizable(False, False)

        self.agent = AdaptiveAgent(order=2)
        self.human_wins = 0
        self.agent_wins = 0
        self.ties = 0
        self.total_rounds = 0
        self.tts_enabled = False

        self._build_ui()
        self._bind_keys()

    def _build_ui(self):
        # Header Frame
        header = tk.Frame(self.root, bg="#0f172a", pady=12)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="Rock-Paper-Scissors AI Arena",
            font=("Helvetica", 18, "bold"),
            fg="#38bdf8",
            bg="#0f172a",
        )
        title.pack()

        subtitle = tk.Label(
            header,
            text="Order-2 Markov Chain Agent • 🎙️ Voice & Accessibility Enabled",
            font=("Helvetica", 10),
            fg="#94a3b8",
            bg="#0f172a",
        )
        subtitle.pack(pady=2)

        # Accessibility Control Bar
        acc_bar = tk.Frame(self.root, bg="#1e293b", padx=15, pady=6)
        acc_bar.pack(fill="x", padx=25, pady=4)

        self.lbl_acc_status = tk.Label(
            acc_bar,
            text="🔇 Spoken Commentary: OFF • Press V to Enable Voice Mode",
            font=("Consolas", 8, "bold"),
            fg="#94a3b8",
            bg="#1e293b",
        )
        self.lbl_acc_status.pack(side="left")

        self.btn_tts_toggle = tk.Button(
            acc_bar,
            text="🎙️ Enable Voice (V)",
            font=("Helvetica", 8, "bold"),
            bg="#0284c7",
            fg="white",
            relief="flat",
            command=self.toggle_tts,
        )
        self.btn_tts_toggle.pack(side="right")

        # Scoreboard Frame
        score_frame = tk.Frame(self.root, bg="#1e293b", padx=15, pady=10, relief="ridge", bd=1)
        score_frame.pack(fill="x", padx=25, pady=8)

        self.lbl_rounds = tk.Label(score_frame, text="Rounds\n0", font=("Helvetica", 12, "bold"), fg="#f8fafc", bg="#1e293b")
        self.lbl_rounds.grid(row=0, column=0, padx=18)

        self.lbl_ai = tk.Label(score_frame, text="AI Wins\n0", font=("Helvetica", 12, "bold"), fg="#ef4444", bg="#1e293b")
        self.lbl_ai.grid(row=0, column=1, padx=18)

        self.lbl_you = tk.Label(score_frame, text="Your Wins\n0", font=("Helvetica", 12, "bold"), fg="#22c55e", bg="#1e293b")
        self.lbl_you.grid(row=0, column=2, padx=18)

        self.lbl_rate = tk.Label(score_frame, text="AI Win%\n0.0%", font=("Helvetica", 12, "bold"), fg="#38bdf8", bg="#1e293b")
        self.lbl_rate.grid(row=0, column=3, padx=18)

        # Arena Display Box
        arena_frame = tk.Frame(self.root, bg="#1e293b", padx=20, pady=12, relief="ridge", bd=1)
        arena_frame.pack(fill="x", padx=25, pady=8)

        self.lbl_player_move = tk.Label(arena_frame, text="YOU\n❓", font=("Helvetica", 14, "bold"), fg="#f8fafc", bg="#1e293b")
        self.lbl_player_move.grid(row=0, column=0, padx=40)

        vs_lbl = tk.Label(arena_frame, text="VS", font=("Helvetica", 16, "bold"), fg="#64748b", bg="#1e293b")
        vs_lbl.grid(row=0, column=1, padx=20)

        self.lbl_ai_move = tk.Label(arena_frame, text="MARKOV AI\n🤖", font=("Helvetica", 14, "bold"), fg="#f8fafc", bg="#1e293b")
        self.lbl_ai_move.grid(row=0, column=2, padx=40)

        # Outcome Banner
        self.lbl_outcome = tk.Label(
            self.root,
            text="Choose your move: Press R, P, or S",
            font=("Helvetica", 11, "bold"),
            fg="#f8fafc",
            bg="#334155",
            pady=8,
        )
        self.lbl_outcome.pack(fill="x", padx=25, pady=6)

        # Buttons Frame
        btn_frame = tk.Frame(self.root, bg="#0f172a")
        btn_frame.pack(pady=8)

        btn_rock = tk.Button(
            btn_frame,
            text="🪨 Rock (R)",
            font=("Helvetica", 11, "bold"),
            bg="#3b82f6",
            fg="white",
            width=13,
            height=2,
            cursor="hand2",
            command=lambda: self.play("R"),
        )
        btn_rock.grid(row=0, column=0, padx=6)

        btn_paper = tk.Button(
            btn_frame,
            text="📄 Paper (P)",
            font=("Helvetica", 11, "bold"),
            bg="#8b5cf6",
            fg="white",
            width=13,
            height=2,
            cursor="hand2",
            command=lambda: self.play("P"),
        )
        btn_paper.grid(row=0, column=1, padx=6)

        btn_scissors = tk.Button(
            btn_frame,
            text="✂️ Scissors (S)",
            font=("Helvetica", 11, "bold"),
            bg="#ec4899",
            fg="white",
            width=13,
            height=2,
            cursor="hand2",
            command=lambda: self.play("S"),
        )
        btn_scissors.grid(row=0, column=2, padx=6)

        # AI Prediction Insight
        self.lbl_prediction = tk.Label(
            self.root,
            text="AI Inference: Waiting for initial moves...",
            font=("Consolas", 9),
            fg="#94a3b8",
            bg="#0f172a",
        )
        self.lbl_prediction.pack(pady=4)

        # History Treeview
        hist_frame = tk.Frame(self.root, bg="#0f172a")
        hist_frame.pack(fill="both", expand=True, padx=25, pady=8)

        columns = ("round", "you", "ai", "pred", "result")
        self.tree = ttk.Treeview(hist_frame, columns=columns, show="headings", height=5)
        self.tree.heading("round", text="Round")
        self.tree.heading("you", text="Your Move")
        self.tree.heading("ai", text="AI Move")
        self.tree.heading("pred", text="AI Predicted")
        self.tree.heading("result", text="Result")

        self.tree.column("round", width=60, anchor="center")
        self.tree.column("you", width=100, anchor="center")
        self.tree.column("ai", width=100, anchor="center")
        self.tree.column("pred", width=110, anchor="center")
        self.tree.column("result", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)

        # Controls Row (Reset + Speak Score)
        ctrl_frame = tk.Frame(self.root, bg="#0f172a")
        ctrl_frame.pack(pady=6)

        btn_score = tk.Button(
            ctrl_frame,
            text="Announce Score (C)",
            font=("Helvetica", 9),
            bg="#0284c7",
            fg="white",
            command=self.announce_score,
            padx=10,
        )
        btn_score.grid(row=0, column=0, padx=6)

        btn_reset = tk.Button(
            ctrl_frame,
            text="Reset Match (X)",
            font=("Helvetica", 9),
            bg="#475569",
            fg="white",
            command=self.reset_game,
            padx=10,
        )
        btn_reset.grid(row=0, column=1, padx=6)

    def _bind_keys(self):
        """Bind accessible hotkeys for keyboard & screen reader players."""
        for r_key in ["<r>", "<R>"]:
            self.root.bind(r_key, lambda e: self.play("R"))
        for p_key in ["<p>", "<P>"]:
            self.root.bind(p_key, lambda e: self.play("P"))
        for s_key in ["<s>", "<S>"]:
            self.root.bind(s_key, lambda e: self.play("S"))
        for c_key in ["<c>", "<C>"]:
            self.root.bind(c_key, lambda e: self.announce_score())
        for x_key in ["<x>", "<X>"]:
            self.root.bind(x_key, lambda e: self.reset_game())
        for m_key in ["<m>", "<M>", "<v>", "<V>"]:
            self.root.bind(m_key, lambda e: self.toggle_tts())

    def toggle_tts(self):
        self.tts_enabled = not self.tts_enabled
        if self.tts_enabled:
            self.btn_tts_toggle.config(text="⏹️ Stop Voice (V)", bg="#dc2626")
            self.lbl_acc_status.config(text="🔊 Voice Commentary: ON • Keys: [R/P/S] Play, [C] Score", fg="#38bdf8")
            speak_async("Voice commentary enabled.")
        else:
            self.btn_tts_toggle.config(text="🎙️ Enable Voice (V)", bg="#0284c7")
            self.lbl_acc_status.config(text="🔇 Voice Commentary: OFF • Press V to Enable Voice Mode", fg="#94a3b8")

    def announce_score(self):
        text = f"Round {self.total_rounds}. You have {self.human_wins} wins, AI has {self.agent_wins} wins, and {self.ties} ties."
        if self.tts_enabled:
            speak_async(text)

    def play(self, move: str):
        emojis = {"R": "🪨", "P": "📄", "S": "✂️"}
        predicted_move = self.agent.model.predict_next_move()
        agent_move = COUNTER_MOVES[predicted_move]
        outcome = evaluate_round(agent_move, move)

        self.agent.observe(move)
        self.total_rounds += 1

        spoken_msg = ""
        if outcome == "WIN":
            self.agent_wins += 1
            res_str = "AI WINS"
            self.lbl_outcome.config(text=f"AI Won! AI predicted {MOVE_NAMES[predicted_move]} and countered with {MOVE_NAMES[agent_move]}", bg="#7f1d1d", fg="#fca5a5")
            spoken_msg = f"You played {MOVE_NAMES[move]}. AI countered with {MOVE_NAMES[agent_move]}. AI wins! Score: You {self.human_wins}, AI {self.agent_wins}."
        elif outcome == "LOSS":
            self.human_wins += 1
            res_str = "YOU WIN"
            self.lbl_outcome.config(text=f"You Won! AI played {MOVE_NAMES[agent_move]}", bg="#14532d", fg="#86efac")
            spoken_msg = f"You played {MOVE_NAMES[move]}. AI played {MOVE_NAMES[agent_move]}. You win! Score: You {self.human_wins}, AI {self.agent_wins}."
        else:
            self.ties += 1
            res_str = "TIE"
            self.lbl_outcome.config(text=f"Tie! Both played {MOVE_NAMES[move]}", bg="#78350f", fg="#fde68a")
            spoken_msg = f"Both played {MOVE_NAMES[move]}. It's a tie! Score: You {self.human_wins}, AI {self.agent_wins}."

        ai_rate = (self.agent_wins / self.total_rounds) * 100

        # Update labels
        self.lbl_rounds.config(text=f"Rounds\n{self.total_rounds}")
        self.lbl_ai.config(text=f"AI Wins\n{self.agent_wins}")
        self.lbl_you.config(text=f"Your Wins\n{self.human_wins}")
        self.lbl_rate.config(text=f"AI Win%\n{ai_rate:.1f}%")

        self.lbl_player_move.config(text=f"YOU\n{emojis[move]} {MOVE_NAMES[move]}")
        self.lbl_ai_move.config(text=f"MARKOV AI\n{emojis[agent_move]} {MOVE_NAMES[agent_move]}")
        self.lbl_prediction.config(text=f"AI Inference: Predicted {MOVE_NAMES[predicted_move]} ({predicted_move}) ➔ Countered with {MOVE_NAMES[agent_move]} ({agent_move})")

        # Insert to history treeview at top
        self.tree.insert("", 0, values=(self.total_rounds, f"{emojis[move]} {move}", f"{emojis[agent_move]} {agent_move}", f"{emojis[predicted_move]} {predicted_move}", res_str))

        if self.tts_enabled:
            speak_async(spoken_msg)

    def reset_game(self):
        self.agent.reset()
        self.human_wins = 0
        self.agent_wins = 0
        self.ties = 0
        self.total_rounds = 0

        self.lbl_rounds.config(text="Rounds\n0")
        self.lbl_ai.config(text="AI Wins\n0")
        self.lbl_you.config(text="Your Wins\n0")
        self.lbl_rate.config(text="AI Win%\n0.0%")
        self.lbl_player_move.config(text="YOU\n❓")
        self.lbl_ai_move.config(text="MARKOV AI\n🤖")
        self.lbl_outcome.config(text="Game reset. Choose your move!", bg="#334155", fg="#f8fafc")
        self.lbl_prediction.config(text="AI Inference: Model reset to initial state.")
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.tts_enabled:
            speak_async("Game reset to round zero. Ready for your move.")


if __name__ == "__main__":
    root = tk.Tk()
    app = RPSDesktopApp(root)
    root.mainloop()
