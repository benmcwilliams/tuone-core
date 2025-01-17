```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Fraunhofer Research Institution for Energy Infrastructures and Geothermal Systems (IEG)"
sort location, dt_announce desc
```
