```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Szegedi-Távfutö-Kft" or company = "Szegedi Távfutö Kft")
sort location, dt_announce desc
```
