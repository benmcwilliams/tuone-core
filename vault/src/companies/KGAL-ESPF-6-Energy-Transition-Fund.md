```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "KGAL-ESPF-6-Energy-Transition-Fund" or company = "KGAL ESPF 6 Energy Transition Fund")
sort location, dt_announce desc
```
