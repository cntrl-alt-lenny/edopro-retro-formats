--Super Vehicroid - Stealth Union (historical implementation, Retro Formats)
--Original script for edopro-retro-formats (MIT). Written from the period card text
--and the engine's Lua API; it is not a copy or an adaptation of any Project Ignis
--CardScripts file, whose licence (AGPL-3.0-or-later) this repository does not carry.
--
--Period text (GLAS-EN041): ""Truckroid" + "Expressroid" + "Drillroid" + "Stealthroid"
--When this card attacks, its original ATK is halved until the end of the Damage Step.
--During battle between this attacking card and a Defense Position monster whose DEF
--is lower than the ATK of this card, inflict the difference as Battle Damage to your
--opponent. Once per turn, you can select 1 monster you control, except a Machine-Type
--monster, and equip it to this card. While equipped by this effect, this card can
--attack all monsters your opponent controls once each."
--
--The one behaviour that differs from the modern card, and the reason this script
--exists: the equip effect only ever selects a monster YOU control. The modern card
--selects any face-up monster on the field, so it can take an opponent's monster.
--See data/custom-cards/c600000002.json for what this script does not reproduce.
local s,id=GetID()
local CARD_TRUCKROID=61538782
local CARD_EXPRESSROID=984114
local CARD_DRILLROID=71218746
local CARD_STEALTHROID=98049038
function s.initial_effect(c)
	c:EnableReviveLimit()
	Fusion.AddProcMix(c,true,true,CARD_TRUCKROID,CARD_EXPRESSROID,CARD_DRILLROID,CARD_STEALTHROID)
	--can only be Special Summoned by a Fusion Summon
	local e0=Effect.CreateEffect(c)
	e0:SetType(EFFECT_TYPE_SINGLE)
	e0:SetProperty(EFFECT_FLAG_CANNOT_DISABLE+EFFECT_FLAG_UNCOPYABLE)
	e0:SetCode(EFFECT_SPSUMMON_CONDITION)
	e0:SetValue(aux.fuslimit)
	c:RegisterEffect(e0)
	--when this card attacks, its original ATK is halved until the end of the Damage Step
	local e1=Effect.CreateEffect(c)
	e1:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_CONTINUOUS)
	e1:SetCode(EVENT_ATTACK_ANNOUNCE)
	e1:SetOperation(s.atkop)
	c:RegisterEffect(e1)
	--piercing battle damage
	local e2=Effect.CreateEffect(c)
	e2:SetType(EFFECT_TYPE_SINGLE)
	e2:SetCode(EFFECT_PIERCE)
	c:RegisterEffect(e2)
	--once per turn: equip 1 non-Machine monster YOU control to this card
	local e3=Effect.CreateEffect(c)
	e3:SetCategory(CATEGORY_EQUIP)
	e3:SetType(EFFECT_TYPE_IGNITION)
	e3:SetRange(LOCATION_MZONE)
	e3:SetProperty(EFFECT_FLAG_CARD_TARGET)
	e3:SetCountLimit(1)
	e3:SetTarget(s.eqtg)
	e3:SetOperation(s.eqop)
	c:RegisterEffect(e3)
	--while equipped by that effect, this card can attack all monsters the opponent controls once each
	local e4=Effect.CreateEffect(c)
	e4:SetType(EFFECT_TYPE_SINGLE)
	e4:SetCode(EFFECT_ATTACK_ALL)
	e4:SetCondition(s.atkallcon)
	e4:SetValue(1)
	c:RegisterEffect(e4)
end
function s.atkop(e,tp,eg,ep,ev,re,r,rp)
	local c=e:GetHandler()
	if not c:IsRelateToBattle() or c:IsFacedown() then return end
	local e1=Effect.CreateEffect(c)
	e1:SetType(EFFECT_TYPE_SINGLE)
	e1:SetProperty(EFFECT_FLAG_CANNOT_DISABLE)
	e1:SetCode(EFFECT_SET_BASE_ATTACK)
	e1:SetValue(c:GetBaseAttack()//2)
	e1:SetReset(RESET_EVENT+RESETS_STANDARD_DISABLE+RESET_PHASE+PHASE_DAMAGE)
	c:RegisterEffect(e1)
end
function s.eqfilter(c)
	return c:IsFaceup() and not c:IsRace(RACE_MACHINE)
end
function s.eqtg(e,tp,eg,ep,ev,re,r,rp,chk,chkc)
	if chkc then return chkc:IsControler(tp) and chkc:IsLocation(LOCATION_MZONE) and s.eqfilter(chkc) end
	if chk==0 then return Duel.GetLocationCount(tp,LOCATION_SZONE)>0
		and Duel.IsExistingTarget(s.eqfilter,tp,LOCATION_MZONE,0,1,nil) end
	Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_EQUIP)
	local g=Duel.SelectTarget(tp,s.eqfilter,tp,LOCATION_MZONE,0,1,1,nil)
	Duel.SetOperationInfo(0,CATEGORY_EQUIP,g,1,0,0)
end
function s.eqop(e,tp,eg,ep,ev,re,r,rp)
	local c=e:GetHandler()
	local tc=Duel.GetFirstTarget()
	if not c:IsRelateToEffect(e) or c:IsFacedown() then return end
	if not tc or not tc:IsRelateToEffect(e) or not s.eqfilter(tc) then return end
	if Duel.GetLocationCount(tp,LOCATION_SZONE)<=0 then return end
	if not Duel.Equip(tp,tc,c) then return end
	--remember that it was equipped by this effect
	tc:RegisterFlagEffect(id,RESET_EVENT+RESETS_STANDARD,0,1)
	--equip limit: only this card
	local e1=Effect.CreateEffect(c)
	e1:SetType(EFFECT_TYPE_SINGLE)
	e1:SetProperty(EFFECT_FLAG_CANNOT_DISABLE)
	e1:SetCode(EFFECT_EQUIP_LIMIT)
	e1:SetReset(RESET_EVENT+RESETS_STANDARD)
	e1:SetLabelObject(c)
	e1:SetValue(s.eqlimit)
	tc:RegisterEffect(e1)
end
function s.eqlimit(e,c)
	return c==e:GetLabelObject()
end
function s.atkallfilter(c)
	return c:GetFlagEffect(id)>0
end
function s.atkallcon(e)
	return e:GetHandler():GetEquipGroup():IsExists(s.atkallfilter,1,nil)
end
