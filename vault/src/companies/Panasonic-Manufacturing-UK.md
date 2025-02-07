```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Panasonic-Manufacturing-UK" or company = "Panasonic Manufacturing UK")
sort location, dt_announce desc
```
