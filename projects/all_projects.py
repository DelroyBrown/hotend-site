from projects.generic.project import generic_project
from projects.hemera.project import hemera_grease_dispenser_project
# from projects.integrated_hotend_press.project import ih_press_project
# from projects.prusa_nube_press.project import prusa_nube_press_project
# from projects.v6_component_qc.project import v6_heater_qc_project, v6_hotend_qc_project, v6_sensor_qc_project
# from projects.v6_hot_tightening.project import v6_hot_tightening_project
from projects.v7_post_curing_qc.project import v7_post_curing_qc_project


PROJECTS = [
    generic_project,
    hemera_grease_dispenser_project,
    # ih_press_project,
    # prusa_nube_press_project,
    # v6_heater_qc_project,
    # v6_hotend_qc_project,
    # v6_hot_tightening_project,
    # v6_sensor_qc_project,
    v7_post_curing_qc_project,
]
