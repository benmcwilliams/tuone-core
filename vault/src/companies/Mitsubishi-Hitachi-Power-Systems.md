```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Mitsubishi-Hitachi-Power-Systems" or company = "Mitsubishi Hitachi Power Systems")
sort location, dt_announce desc
```
