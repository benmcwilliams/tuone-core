```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Eavor-Erdwärme-Geretsried-GmbH" or company = "Eavor Erdwärme Geretsried GmbH")
sort location, dt_announce desc
```
