```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "SAG-Solarstrom" or company = "SAG Solarstrom")
sort location, dt_announce desc
```
