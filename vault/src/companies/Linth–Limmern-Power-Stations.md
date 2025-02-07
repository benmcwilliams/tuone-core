```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Linth–Limmern-Power-Stations" or company = "Linth–Limmern Power Stations")
sort location, dt_announce desc
```
