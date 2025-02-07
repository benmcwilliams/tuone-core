```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Research-Infrastructure-for-Geothermal-Energy-(RINGEN)" or company = "Research Infrastructure for Geothermal Energy (RINGEN)")
sort location, dt_announce desc
```
