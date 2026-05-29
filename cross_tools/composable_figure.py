from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

from matplotlib.patches import Patch
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np
import pandas as pd


@dataclass
class Entry:
    value: str | int
    displayed_value: str | int = ""
    color: str = ""

@dataclass
class ColumnFilter:
    column_name: str = ""
    entries: list[Entry] = field(default_factory=list)

class ComposableFigure:
    def __init__(self, data: pd.DataFrame):
        self._data: pd.DataFrame = data
        self._panels: ColumnFilter = ColumnFilter()
        self._columns: ColumnFilter = ColumnFilter()
        self._groups: ColumnFilter = ColumnFilter()
        self._variables: ColumnFilter = ColumnFilter()

        # Colorblind colors pre selected by matplotlib
        # https://matplotlib.org/stable/users/prev_whats_new/whats_new_2.2.html#new-style-colorblind-friendly-color-cycle
        plt.style.use("tableau-colorblind10")
        self._colorblind_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    def _get_colorblind_colors(self) -> Generator[str, None, None]:
        for color in self._colorblind_colors:
            yield color

    def _get_unique_values_in_data(
        self,
        column_filter: ColumnFilter,
        give_color: bool = False,
    ) -> list[Entry]:
        if column_filter.column_name == "":
            output = list()
        elif not any(column_filter.entries):
            output = [
                Entry(
                    value=value,
                    displayed_value=value
                )
                for value in self._data[column_filter.column_name].unique()
            ]
        else:
            output = [
                entry
                for entry in column_filter.entries
                if entry.value in self._data[column_filter.column_name].values
            ]
        colors = self._get_colorblind_colors()
        for entry in output:
            if entry.displayed_value == "":
                entry.displayed_value = entry.value
            if give_color and entry.color == "":
                entry.color = next(colors)
        return output
    
    def configure_panels(self, from_table_column: ColumnFilter):
        self._panels = from_table_column

    @property
    def panels(self):
        return self._get_unique_values_in_data(self._panels)

    def configure_columns(self, from_table_column: ColumnFilter):
        self._columns = from_table_column

    @property
    def columns(self):
        return self._get_unique_values_in_data(self._columns)
    
    def configure_groups(self, from_table_column: ColumnFilter):
        self._groups = from_table_column

    @property
    def groups(self):
        return self._get_unique_values_in_data(self._groups)
    
    def configure_variables(self, from_table_column: ColumnFilter):
        self._variables = from_table_column

    @property
    def variables(self):
        return self._get_unique_values_in_data(self._variables, give_color=True)
    
    def _compose(self, y_min: float, y_max: float, y_step: float):
        panels = self.panels
        columns = self.columns
        groups = self.groups
        variables = self.variables

        self._fig, self._axes = plt.subplots(
            nrows=max(1, len(panels)),
            ncols=max(1, len(columns)),
            figsize=(7, 5),
            sharex=True,
            sharey=True
        )
        plt.subplots_adjust(
            # hspace=0,
            wspace=0
        )

        for panel_index in range(len(panels)):
            TOP_PANEL = 0
            BOTTOM_PANEL = max(0, len(panels) - 1)
            for column_index in range(len(columns)):
                LEFT_COLUMN = 0
                RIGHT_COLUMN = max(0, len(columns) - 1)
                if len(panels) == 1:
                    panel_axes = self._axes
                else:
                    panel_axes = self._axes[panel_index]
                if len(columns) == 1:
                    ax: Axes = panel_axes
                else:
                    ax: Axes = panel_axes[column_index]

                ax.grid(axis='y', linestyle='--', alpha=0.6)
                ax.set_ylim(y_min)
                y_ticks = np.arange(y_min, y_max + y_step, y_step)
                ax.set_yticks(y_ticks)
                ax.axhline(0, color="black", linewidth=0.5, zorder=5)

                if panel_index != TOP_PANEL:
                    ax.spines["top"].set_visible(False)

                if panel_index == TOP_PANEL:
                    ax.set_title(str(columns[column_index].displayed_value))

                if panel_index != BOTTOM_PANEL:
                    ax.spines["bottom"].set_visible(False)
                    ax.tick_params(
                        axis="x",
                        which="both",
                        bottom=False
                    )

                group_width = len(variables) + 1
                group_positions = np.linspace(
                    (len(variables)-1)/2,
                    (len(variables)-1)/2 + group_width * (len(groups)-1),
                    len(groups)
                )
                if panel_index == BOTTOM_PANEL:
                    ax.set_xticks(group_positions)
                    ax.set_xticklabels([str(group.displayed_value) for group in groups])

                if column_index != LEFT_COLUMN:
                    ax.tick_params(
                        axis="y",
                        which="both",
                        left=False
                    )
                    ax.spines["left"].set_visible(False)

                if column_index != RIGHT_COLUMN:
                    ax.spines["right"].set(
                        color="gray",
                        linestyle="--",
                        linewidth=1,
                        alpha=0.5,
                    )

                if column_index == RIGHT_COLUMN:
                    ax.yaxis.set_label_position("right")
                    ax.set_ylabel(str(panels[panel_index].displayed_value))
                
                for group_index in range(len(groups)):
                    for variable_index in range(len(variables)):
                        data_to_plot = self._data.copy()
                        data_to_plot = data_to_plot[
                            (data_to_plot[self._panels.column_name] == panels[panel_index].value)
                            & (data_to_plot[self._columns.column_name] == columns[column_index].value)
                            & (data_to_plot[self._groups.column_name] == groups[group_index].value)
                            & (data_to_plot[self._variables.column_name] == variables[variable_index].value)
                        ]
                        ax.bar(
                            x=group_index * group_width + variable_index,
                            height=data_to_plot.value,
                            width=0.9,
                            facecolor=variables[variable_index].color,
                        )


    def plot(
        self,
        title: str = "",
        y_label: str = "",
        y_min: int = -20,
        y_max: float = 20,
        y_step: float = 5,
    ):
        self._compose(
            y_min=y_min,
            y_max=y_max,
            y_step=y_step,
        )
        
        self._fig.suptitle(title)
        self._fig.text(
            x=0.04,
            y=0.5,
            s=y_label,
            va='center',
            rotation='vertical'
        )
        variables = self.variables
        handles = [
            Patch(
                label=variable.displayed_value,
                facecolor=variable.color
            )
            for variable in variables
        ]
        self._fig.legend(
            handles=handles,
            loc='center left',
            bbox_to_anchor=(0.92, 0.5)
        )

        plt.show()

    def save(
        self,
        file_path: str | Path
    ):
        self._fig.savefig(
            file_path,
            bbox_inches="tight",
            dpi=300,
        )