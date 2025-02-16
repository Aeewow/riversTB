import tkinter as tk
from tkinter import ttk
import pandas as pd
from main import cluster_dbscan, perform_clustering

class BuildingFilterApp:
    def __init__(self, master):
        self.master = master
        master.title("Building Filter")

        # Load data from Excel
        self.data = pd.read_excel('data2.xlsx')
        self.street_names = self.data['Улица'].unique().tolist()
        self.selected_streets = []

        # Label
        self.label = ttk.Label(master, text="Select Street:")
        self.label.pack(pady=10)

        # Combobox for single street selection
        self.street_combobox = ttk.Combobox(master, values=self.street_names)
        self.street_combobox.pack(pady=5)

        # Button to open multiple street selection window
        self.multiple_button = ttk.Button(master, text="Выбрать несколько улиц", command=self.open_multiple_selection)
        self.multiple_button.pack(pady=10)

        # Button to clear street selection
        self.clear_selection_button = ttk.Button(master, text="Отменить выбор", command=self.clear_selection)
        self.clear_selection_button.pack(pady=10)

        # Cluster Button
        self.cluster_button = ttk.Button(master, text="Кластеризовать здания", command=self.cluster_buildings)
        self.cluster_button.pack(pady=10)

        # Show Buildings Button
        self.show_button = ttk.Button(master, text="Показать здания", command=self.show_buildings)
        self.show_button.pack(pady=10)

        # Transfer Coordinates Button
        self.transfer_button = ttk.Button(master, text="Передать координаты", command=self.transfer_coordinates)
        self.transfer_button.pack(pady=10)

        # Result List
        self.result_list = tk.Listbox(master, height=10, width=50)
        self.result_list.pack(pady=10)

    def cluster_buildings(self):
        if len(self.selected_streets) <= 1:
            print("Warning: Please select more than one street for clustering.")
            return

        from main import perform_clustering
        perform_clustering(self.selected_streets)

    def open_multiple_selection(self):
        # Create a new window for multiple street selection
        multiple_window = tk.Toplevel(self.master)
        multiple_window.title("Select Multiple Streets")

        # Listbox for multiple street selection
        street_listbox = tk.Listbox(multiple_window, selectmode=tk.MULTIPLE, height=15, width=50)
        for street in self.street_names:
            street_listbox.insert(tk.END, street)
        street_listbox.pack(pady=5)

        # Button to confirm selection
        confirm_button = ttk.Button(multiple_window, text="Confirm Selection", command=lambda: self.confirm_selection(street_listbox, multiple_window))
        confirm_button.pack(pady=10)

    def confirm_selection(self, street_listbox, window):
        selected_indices = street_listbox.curselection()
        self.selected_streets = [street_listbox.get(i) for i in selected_indices]
        print("Selected streets:", self.selected_streets)
        window.destroy()

    def clear_selection(self):
        self.selected_streets = []
        self.result_list.delete(0, tk.END)  # Clear the result list
        self.street_combobox.set('')  # Clear the combobox selection
        print("Street selection cleared.")

    def show_buildings(self):
        if self.selected_streets:
            filtered_data = self.data[self.data['Улица'].isin(self.selected_streets)]
        else:
            selected_street = self.street_combobox.get()
            filtered_data = self.data[self.data['Улица'] == selected_street]
        buildings = filtered_data['Номер дома'].tolist()

        self.result_list.delete(0, tk.END)
        for building in buildings:
            self.result_list.insert(tk.END, building)

    def transfer_coordinates(self):
        if self.selected_streets:
            filtered_data = self.data[self.data['Улица'].isin(self.selected_streets)]
        else:
            selected_street = self.street_combobox.get()
            filtered_data = self.data[self.data['Улица'] == selected_street]
        coordinates = filtered_data[['Широта', 'Долгота']]

        # Clear existing data and write new coordinates to clustered_buildings.csv
        coordinates.to_csv('clustered_buildings.csv', mode='w', header=['Широта', 'Долгота'], index=False)
        print("Coordinates successfully written to clustered_buildings.csv")

if __name__ == "__main__":
    root = tk.Tk()
    app = BuildingFilterApp(root)
    root.mainloop()
