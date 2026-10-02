import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json

class MDMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Entity360 MDM Configuration")
        self.root.geometry("600x400")

        self.config_data = {
            "policies": [],
            "constraints": []
        }

        self.show_login()

    def show_login(self):
        self.clear_window()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

        ttk.Label(frame, text="Login", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="Username:").grid(row=1, column=0, pady=5, sticky="e")
        self.username_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.username_var).grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Password:").grid(row=2, column=0, pady=5, sticky="e")
        self.password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.password_var, show="*").grid(row=2, column=1, pady=5)

        ttk.Button(frame, text="Login", command=self.do_login).grid(row=3, column=0, columnspan=2, pady=15)

    def do_login(self):
        import os
        user = self.username_var.get()
        pwd = self.password_var.get()

        expected_user = os.environ.get("MDM_ADMIN_USER")
        expected_pwd = os.environ.get("MDM_ADMIN_PWD")

        if not expected_user or not expected_pwd:
            messagebox.showerror("Error", "Server configuration error: Authentication not configured.")
            return

        if user == expected_user and pwd == expected_pwd:
            self.show_main_menu()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def show_main_menu(self):
        self.clear_window()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="MDM Configuration", font=("Arial", 16)).pack(pady=10)

        ttk.Button(frame, text="Add Source Pair Policy", command=self.show_add_policy).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text="Add Cluster Constraint", command=self.show_add_constraint).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text="View/Export Config", command=self.show_config).pack(pady=5, fill=tk.X)
        ttk.Button(frame, text="Logout", command=self.show_login).pack(pady=20, fill=tk.X)

    def show_add_policy(self):
        self.clear_window()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Add Source Pair Policy", font=("Arial", 14)).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="Left Source:").grid(row=1, column=0, pady=5, sticky="e")
        left_src_var = tk.StringVar()
        ttk.Entry(frame, textvariable=left_src_var).grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Right Source:").grid(row=2, column=0, pady=5, sticky="e")
        right_src_var = tk.StringVar()
        ttk.Entry(frame, textvariable=right_src_var).grid(row=2, column=1, pady=5)

        def save_policy():
            pol = {
                "left_source": left_src_var.get(),
                "right_source": right_src_var.get(),
                "mandatory_gates": [],
                "qualifying_clauses": []
            }
            self.config_data["policies"].append(pol)
            messagebox.showinfo("Success", "Policy added (basic shell). Edit JSON for conditions.")
            self.show_main_menu()

        ttk.Button(frame, text="Save", command=save_policy).grid(row=3, column=0, pady=15)
        ttk.Button(frame, text="Cancel", command=self.show_main_menu).grid(row=3, column=1, pady=15)

    def show_add_constraint(self):
        self.clear_window()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Add Cluster Constraint", font=("Arial", 14)).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="Target Source:").grid(row=1, column=0, pady=5, sticky="e")
        target_src_var = tk.StringVar()
        ttk.Entry(frame, textvariable=target_src_var).grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Max Records:").grid(row=2, column=0, pady=5, sticky="e")
        max_rec_var = tk.IntVar(value=1)
        ttk.Entry(frame, textvariable=max_rec_var).grid(row=2, column=1, pady=5)

        def save_constraint():
            con = {
                "target_source": target_src_var.get(),
                "max_records": max_rec_var.get()
            }
            self.config_data["constraints"].append(con)
            messagebox.showinfo("Success", "Constraint added.")
            self.show_main_menu()

        ttk.Button(frame, text="Save", command=save_constraint).grid(row=3, column=0, pady=15)
        ttk.Button(frame, text="Cancel", command=self.show_main_menu).grid(row=3, column=1, pady=15)

    def show_config(self):
        self.clear_window()

        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Current Configuration", font=("Arial", 14)).pack(pady=10)

        text_area = tk.Text(frame, height=15, width=60)
        text_area.pack(pady=5)
        text_area.insert(tk.END, json.dumps(self.config_data, indent=2))

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save to File", command=self.save_to_file).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Back", command=self.show_main_menu).pack(side=tk.LEFT, padx=10)

    def save_to_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Configuration As"
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(self.config_data, f, indent=2)
                messagebox.showinfo("Success", f"Configuration saved successfully to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MDMApp(root)
    root.mainloop()
