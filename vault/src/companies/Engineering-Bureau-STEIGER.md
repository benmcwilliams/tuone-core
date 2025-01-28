```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Engineering-Bureau-STEIGER" or company = "Engineering Bureau STEIGER")
sort location, dt_announce desc
```
