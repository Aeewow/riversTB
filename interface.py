import tkinter as tk
from tkinter import ttk
import pandas as pd
import json
import glob
from main import perform_clustering, save_coordinates

class BuildingFilterApp:
    def __init__(self, master):
        self.master = master
        master.title("Building Filter")

        # Load data from JSON files
        self.data = self.load_json_data()
        self.street_names = sorted(self.data['Улица'].unique().tolist())
        self.selected_streets = []

        # Label
        self.label = ttk.Label(master, text="Select Street:")
        self.label.pack(pady=10)

        # Combobox for single street selection
        self.street_combobox = ttk.Combobox(master, values=self.street_names)
        self.street_combobox.pack(pady=5)

        # Buttons frame
        self.buttons_frame = ttk.Frame(master)
        self.buttons_frame.pack(pady=10)

        # Save coordinates button
        self.save_button = ttk.Button(
            self.buttons_frame,
            text="Передать координаты",
            command=self.save_coordinates_and_reset_clusters
        )
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Clustering button
        self.cluster_button = ttk.Button(
            self.buttons_frame,
            text="Кластеризовать здания",
            command=self.perform_clustering_and_save
        )
        self.cluster_button.pack(side=tk.LEFT, padx=5)

        # Multiple selection button
        self.multiple_button = ttk.Button(
            self.buttons_frame,
            text="Выбрать несколько улиц",
            command=self.open_multiple_selection
        )
        self.multiple_button.pack(side=tk.LEFT, padx=5)

        # Clear selection button
        self.clear_button = ttk.Button(
            self.buttons_frame,
            text="Отменить выбор",
            command=self.clear_selection
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Show buildings button
        self.show_button = ttk.Button(
            self.buttons_frame,
            text="Показать здания",
            command=self.show_buildings
        )
        self.show_button.pack(side=tk.LEFT, padx=5)

        # Result List
        self.result_list = tk.Listbox(master, height=10, width=50)
        self.result_list.pack(pady=10)

        # Bind selection event
        self.street_combobox.bind('<<ComboboxSelected>>', self.on_select)

    def load_json_data(self):
        data_list = []
        json_files = glob.glob("buildsKirovsk_json/*.json")
        print("Found JSON files:", json_files)
        
        for file in json_files:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'result' in data and 'items' in data['result']:
                    for building in data['result']['items']:
                        if isinstance(building, dict):
                            # Ensure we're extracting streets, not organizations or other entities
                            if 'address' in building and 'components' in building['address']:
                                # Extract street name from address components
                                street_components = [comp for comp in building['address']['components'] if comp['type'] == 'street_number']
                                if street_components:
                                    street_name = street_components[0].get('street', '')
                                    
                                    # Check for 'geometry' key
                                    if 'geometry' in building:
                                        centroid = building['geometry']['centroid']
                                        lon, lat = centroid.replace('POINT(', '').replace(')', '').split()
                                        
                                        building_data = {
                                            'Улица': street_name,
                                            'Номер дома': street_components[0].get('number', ''),
                                            'Широта': float(lat),
                                            'Долгота': float(lon)
                                        }
                                        print("Extracted building data:", building_data)
                                        data_list.append(building_data)
                                    else:
                                        print(f"No 'geometry' key in building: {building}")
                            else:
                                print(f"No valid address components in building: {building}")
                        else:
                            print(f"Unexpected data format in {file}: {building}")
                else:
                    print(f"No 'result' or 'items' key in {file}")
        
        df = pd.DataFrame(data_list)
        
        return df

    def on_select(self, event):
        selected_street = self.street_combobox.get()
        if selected_street:
            self.selected_streets = [selected_street]
        else:
            self.selected_streets = []

    def clear_selection(self):
        self.selected_streets = []
        self.result_list.delete(0, tk.END)  # Clear the result list
        self.street_combobox.set('')  # Clear the combobox selection
        print("Street selection cleared.")

    def show_buildings(self):
        selected_street = self.street_combobox.get()
        if not selected_street and not self.selected_streets:
            print("Warning: Please select at least one street.")
            return

        if self.selected_streets:
            filtered_data = self.data[self.data['Улица'].isin(self.selected_streets)]
        else:
            filtered_data = self.data[self.data['Улица'] == selected_street]
        
        buildings = filtered_data['Номер дома'].tolist()

        self.result_list.delete(0, tk.END)
        for building in buildings:
            self.result_list.insert(tk.END, building)

    def save_coordinates_and_reset_clusters(self):
        selected_street = self.street_combobox.get()
        if not selected_street and not self.selected_streets:
            print("Warning: Please select at least one street.")
            return
        
        if not self.selected_streets:
            self.selected_streets = [selected_street]
        
        save_coordinates(self.selected_streets)
        print("Coordinates saved with cluster=0")

    def perform_clustering_and_save(self):
        if len(self.selected_streets) < 2:
            print("Warning: Please select more than one street for clustering.")
            return

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

if __name__ == "__main__":
    root = tk.Tk()
    app = BuildingFilterApp(root)
    root.mainloop()
